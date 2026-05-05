"""Validate local environment for Synthera World beta."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _check_python() -> bool:
    major, minor = sys.version_info[:2]
    ok = (major, minor) == (3, 10)
    print(f"[python] {major}.{minor} {'OK' if ok else 'EXPECTED 3.10'}")
    return ok


def _check_isaac_path() -> bool:
    isaac_path = os.getenv("ISAAC_SIM_PATH", "")
    if not isaac_path:
        print("[isaac] ISAAC_SIM_PATH is not set")
        return False
    path = Path(isaac_path).expanduser()
    ok = path.exists()
    print(f"[isaac] {path} {'OK' if ok else 'MISSING'}")
    return ok


def _check_cuda() -> bool:
    try:
        subprocess.run(["nvidia-smi"], check=True, capture_output=True, text=True)
        print("[cuda] nvidia-smi OK")
        return True
    except Exception:
        print("[cuda] nvidia-smi not available")
        return False


if __name__ == "__main__":
    checks = [_check_python(), _check_isaac_path(), _check_cuda()]
    if all(checks):
        print("Environment validation passed.")
        raise SystemExit(0)
    print("Environment validation failed.")
    raise SystemExit(1)
