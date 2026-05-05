"""Isaac Sim subprocess runner with streaming output."""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import AsyncGenerator


class IsaacRunner:
    """Manages one Isaac Sim subprocess and provides log streaming."""

    def __init__(self) -> None:
        self._process: asyncio.subprocess.Process | None = None
        self._lock = asyncio.Lock()

    async def is_running(self) -> bool:
        """Return True when simulation subprocess is active."""
        return self._process is not None and self._process.returncode is None

    async def stop(self) -> bool:
        """Stop active subprocess, if any."""
        if not await self.is_running():
            return False
        assert self._process is not None
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=5)
        except asyncio.TimeoutError:
            self._process.kill()
            await self._process.wait()
        return True

    async def stream_run(self, script_path: str) -> AsyncGenerator[str, None]:
        """Run Isaac script and stream stdout/stderr lines."""
        async with self._lock:
            if await self.is_running():
                yield "event: error\ndata: Simulation already running\n\n"
                return

            runner = os.getenv("ISAAC_SIM_PYTHON")
            if not runner:
                yield "event: error\ndata: ISAAC_SIM_PYTHON is not configured\n\n"
                return

            script_file = Path(script_path)
            if not script_file.exists():
                yield f"event: error\ndata: Script does not exist: {script_path}\n\n"
                return

            # Dev shortcut: ISAAC_SIM_PYTHON=echo
            command = [runner, str(script_file)]
            if runner == "echo":
                command = ["echo", f"[dry-run] Would execute {script_file}"]

            self._process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            started = time.monotonic()
            timeout_seconds = 300
            saw_traceback = False

            assert self._process.stdout is not None
            try:
                while True:
                    if time.monotonic() - started > timeout_seconds:
                        self._process.terminate()
                        yield "event: error\ndata: Simulation timed out after 300s\n\n"
                        break

                    line = await self._process.stdout.readline()
                    if not line:
                        break
                    text = line.decode(errors="replace").rstrip("\n")
                    if "Traceback (most recent call last)" in text or "ImportError:" in text:
                        saw_traceback = True
                    yield f"data: {text}\n\n"

                code = await self._process.wait()
                if code == 0 and saw_traceback:
                    code = 1
                yield f"event: done\ndata: exit_code={code}\n\n"
            finally:
                self._process = None
