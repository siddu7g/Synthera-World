"""Prompt assembly for Synthera World generate API."""

from __future__ import annotations

import json
import os
from pathlib import Path

from models.sim_config import SimConfig


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
API_REFERENCE_PATH = DATA_DIR / "api_reference.json"
ASSET_CATALOG_PATH = DATA_DIR / "asset_catalog.json"
FALLBACK_ASSET_CATALOG = {
    "humanoid": [
        {"name": "Unitree H1", "asset_path": "/Isaac/Robots/Unitree/H1/h1.usd"},
    ],
    "amr": [
        {
            "name": "Clearpath Ridgeback",
            "asset_path": "/Isaac/Robots/Clearpath/Ridgeback/ridgeback.usd",
        },
        {"name": "Clearpath Jackal", "asset_path": "/Isaac/Robots/Clearpath/Jackal/jackal.usd"},
        {"name": "NVIDIA Carter v1", "asset_path": "/Isaac/Robots/Carter/carter_v1.usd"},
    ],
}


def _read_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_system_prompt() -> str:
    """Build and return the system prompt string."""
    api_reference = _read_json_file(API_REFERENCE_PATH)
    asset_catalog = _read_json_file(ASSET_CATALOG_PATH)
    if not asset_catalog.get("humanoid") and not asset_catalog.get("amr"):
        asset_catalog = FALLBACK_ASSET_CATALOG
    humanoid_mode = os.getenv("HUMANOID_SCRIPT_MODE", "standalone").strip().lower()
    if humanoid_mode not in {"standalone", "basesample"}:
        humanoid_mode = "standalone"

    if humanoid_mode == "basesample":
        mode_rules = (
            "HUMANOID SCRIPT MODE: BaseSample extension.\n"
            "- For humanoid requests, output class HumanoidExample(BaseSample).\n"
            "- Do NOT use SimulationApp wrappers, standalone world.step loops, or simulation_app.close().\n"
            "- Use methods: __init__, setup_scene, setup_post_load, setup_post_reset, "
            "on_physics_step, _timeline_timer_callback_fn, world_cleanup.\n"
            "- Use imports: carb, numpy, omni, omni.appwindow, BaseSample, "
            "H1FlatTerrainPolicy, get_assets_root_path.\n\n"
        )
    else:
        mode_rules = (
            "HUMANOID SCRIPT MODE: standalone SimulationApp script.\n"
            "- SimulationApp must be instantiated BEFORE any other isaacsim import.\n"
            "- Always call simulation_app.close() in a finally block.\n"
            "- Never use time.sleep() - use world.step() for timing.\n\n"
        )

    return (
        "You are an expert NVIDIA Isaac Sim 4.5 Python script generator for Synthera World.\n"
        "You write clean, correct, immediately runnable Isaac Sim Python scripts.\n\n"
        "STRICT RULES:\n"
        "1. Only use APIs from ALLOWED API SURFACE below. Never invent methods.\n"
        "2. Follow HUMANOID SCRIPT MODE rules below.\n"
        "3. All asset paths must come exactly from ASSET CATALOG below.\n"
        "4. Never use deprecated omni.isaac.* namespace. Use isaacsim.* only.\n"
        "5. Never use time.sleep() - use world/world-callback stepping for timing.\n"
        "6. Keep generated output consistent with the requested runtime mode.\n"
        "7. Return only the Python script. No markdown, no explanation, no preamble.\n\n"
        "8. Do NOT include chain-of-thought or reasoning text.\n"
        "9. Do NOT use any /Isaac/Environments/* USD path unless explicitly present in ASSET CATALOG.\n"
        "10. You may call world.scene.add_default_ground_plane() for environment setup.\n\n"
        f"{mode_rules}"
        "ALLOWED API SURFACE:\n"
        f"{json.dumps(api_reference, indent=2)}\n\n"
        "ASSET CATALOG:\n"
        f"{json.dumps(asset_catalog, indent=2)}\n"
    )


def build_user_prompt(config: SimConfig) -> str:
    """Build and return request-specific user prompt."""
    humanoid_mode = os.getenv("HUMANOID_SCRIPT_MODE", "standalone").strip().lower()
    step_hz = 200 if (humanoid_mode == "basesample" and config.robot.category == "humanoid") else 60
    duration_steps = config.task.duration_seconds * step_hz
    return (
        "Generate an Isaac Sim Python script:\n\n"
        f"Robot: {config.robot.category} - {config.robot.asset_name}\n"
        f"Asset path: {config.robot.asset_path}\n"
        f"Environment: {config.scene.environment}, lighting: {config.scene.lighting}, "
        f"obstacles: {config.scene.obstacles}\n"
        f"Task: {config.task.description}\n"
        f"Duration: {duration_steps} steps ({config.task.duration_seconds}s at {step_hz}Hz)\n"
        f"Sensors: camera={config.sensors.camera}, imu={config.sensors.imu}, "
        f"lidar={config.sensors.lidar}\n"
        f"Headless: {config.output.headless}\n"
    )
