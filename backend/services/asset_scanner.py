"""Asset scanner and catalog loader for supported robots."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


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


def scan_assets() -> dict[str, list[dict[str, str]]]:
    """Scan local Isaac install and return available supported assets."""
    isaac_root = Path(
        os.getenv("ISAAC_ASSETS_ROOT") or os.getenv("ISAAC_SIM_PATH", "")
    ).expanduser()
    if not isaac_root.exists():
        return {"humanoid": [], "amr": []}

    catalog: dict[str, list[dict[str, str]]] = {"humanoid": [], "amr": []}
    for category, items in SUPPORTED.items():
        for name, asset_path in items.items():
            if _asset_exists(isaac_root, asset_path):
                catalog[category].append({"name": name, "asset_path": asset_path})
    return catalog


def catalog_path() -> Path:
    """Return local asset catalog path."""
    return Path(__file__).resolve().parent.parent / "data" / "asset_catalog.json"


def load_asset_catalog() -> dict[str, Any]:
    """Load asset catalog JSON from disk; fallback to fresh scan."""
    path = catalog_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return scan_assets()
