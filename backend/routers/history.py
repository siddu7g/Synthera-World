"""History route for simulation records."""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlmodel import Session, select

from models.database import SimulationRecord

router = APIRouter()


@router.get("/simulations")
async def get_simulations(request: Request) -> list[SimulationRecord]:
    """Return simulation history ordered by newest first."""
    engine = request.app.state.db_engine
    with Session(engine) as session:
        statement = select(SimulationRecord).order_by(SimulationRecord.created_at.desc())
        return list(session.exec(statement))
