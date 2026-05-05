"""Simulation routes with SSE log streaming."""

from __future__ import annotations

import time
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from models.database import SimulationRecord

router = APIRouter()


class SimulateRequest(BaseModel):
    generation_id: str


async def _event_stream(request: Request, generation_id: str) -> AsyncGenerator[str, None]:
    engine = request.app.state.db_engine
    runner = request.app.state.isaac_runner
    started = time.monotonic()

    with Session(engine) as session:
        record = session.get(SimulationRecord, generation_id)
        if not record:
            yield "event: error\ndata: generation_id not found\n\n"
            return
        record.status = "running"
        session.add(record)
        session.commit()
        script_path = record.script_path

    exit_code = 1
    async for chunk in runner.stream_run(script_path=script_path):
        if chunk.startswith("event: done"):
            marker = "exit_code="
            if marker in chunk:
                try:
                    exit_code = int(chunk.split(marker, 1)[1].split("\n", 1)[0].strip())
                except ValueError:
                    exit_code = 1
        yield chunk

    duration = time.monotonic() - started
    with Session(engine) as session:
        record = session.get(SimulationRecord, generation_id)
        if record:
            record.duration_s = duration
            record.exit_code = exit_code
            record.status = "complete" if exit_code == 0 else "failed"
            session.add(record)
            session.commit()


@router.post("/simulate")
async def simulate(payload: SimulateRequest, request: Request) -> StreamingResponse:
    """Run a generated script and stream logs via SSE."""
    runner = request.app.state.isaac_runner
    if await runner.is_running():
        raise HTTPException(status_code=409, detail="Simulation already running.")

    stream = _event_stream(request=request, generation_id=payload.generation_id)
    return StreamingResponse(stream, media_type="text/event-stream")


@router.post("/simulate/stop")
async def stop_simulation(request: Request) -> dict[str, bool]:
    """Stop currently active simulation if running."""
    stopped = await request.app.state.isaac_runner.stop()
    return {"stopped": stopped}
