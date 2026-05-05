"""Scan Isaac Sim install for supported humanoid and AMR assets."""

from __future__ import annotations

import json
import os
from pathlib import Path


SUPPORTED = {
    "humanoid": {
        "Unitree H1": "/Isaac/Robots/Unitree/H1/h1.usd",
    },
    "amr": {
        "Clearpath Ridgeback": "/Isaac/Robots/Clearpath/Ridgeback/ridgeback.usd",
        "Clearpath Jackal": "/Isaac/Robots/Clearpath/Jackal/jackal.usd",
        "NVIDIA Carter v1": "/Isaac/Robots/Carter/carter_v1.usd",
    },
}


def _asset_exists(isaac_root: Path, nucleus_path: str) -> bool:
    relative = nucleus_path.lstrip("/")
    return (isaac_root / relative).exists()


def scan_assets(isaac_root: Path) -> dict:
    """Build a filtered catalog with only assets available locally."""
    catalog = {"humanoid": [], "amr": []}
    for category, items in SUPPORTED.items():
        for name, path in items.items():
            if _asset_exists(isaac_root, path):
                catalog[category].append({"name": name, "asset_path": path})
    return catalog


if __name__ == "__main__":
    isaac_path = os.getenv("ISAAC_ASSETS_ROOT") or os.getenv("ISAAC_SIM_PATH")
    if not isaac_path:
        raise SystemExit("ISAAC_ASSETS_ROOT or ISAAC_SIM_PATH is required.")

    isaac_root = Path(isaac_path).expanduser()
    if not isaac_root.exists():
        raise SystemExit(f"ISAAC_SIM_PATH does not exist: {isaac_root}")

    output_path = (
        Path(__file__).resolve().parent.parent / "backend" / "data" / "asset_catalog.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(scan_assets(isaac_root), indent=2),
        encoding="utf-8",
    )
    print(f"Wrote asset catalog to {output_path}")
