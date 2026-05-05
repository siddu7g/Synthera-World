"""Assets route for available robot USDs."""

from __future__ import annotations

from fastapi import APIRouter

from services.asset_scanner import load_asset_catalog

router = APIRouter()


@router.get("/assets")
async def get_assets() -> dict:
    """Return available local humanoid and AMR assets."""
    return load_asset_catalog()
