"""Generate route: SimConfig -> Isaac Sim Python script."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import Session

from models.database import SimulationRecord
from models.responses import GenerateResponse
from models.sim_config import SimConfig
from services.ai_client import AIClient
from services.prompt_builder import build_user_prompt
from services.rag_service import format_rag_chunks_for_prompt, merge_rag_chunks_unique
from services.script_validator import ScriptValidationError, validate_script

router = APIRouter()


def _rag_for_generate_enabled() -> bool:
    return os.getenv("RAG_FOR_GENERATE", "true").strip().lower() in ("1", "true", "yes", "on")


def _rag_generate_top_k() -> int:
    raw = os.getenv("RAG_GENERATE_TOP_K", "6").strip()
    try:
        k = int(raw)
    except ValueError:
        return 6
    return max(1, min(k, 12))


def _rag_query_from_config(config: SimConfig) -> str:
    return (
        f"{config.robot.category} {config.robot.asset_name} {config.robot.asset_path} "
        f"{config.task.description} Isaac Sim humanoid H1 walk policy physics ground plane Unitree"
    )


def _retrieve_chunks_for_generate(request: Request, config: SimConfig) -> str:
    """Optional local RAG context appended to the generate user prompt."""
    if not _rag_for_generate_enabled():
        return ""

    rag = request.app.state.rag_service
    top_k = _rag_generate_top_k()
    primary = rag.retrieve(_rag_query_from_config(config), top_k=top_k)

    merged = list(primary)
    if config.robot.category == "humanoid":
        extra = rag.retrieve(
            "HumanoidExample H1FlatTerrainPolicy BaseSample physics_step walk_cmd "
            "timeline initialize post_reset defaultGroundPlane H1_Governed H1_Ungoverned",
            top_k=4,
        )
        merged = merge_rag_chunks_unique(extra + primary, max_total=min(top_k + 4, 12))

    ctx = format_rag_chunks_for_prompt(merged)
    if not ctx.strip():
        return ""
    return (
        "\n\n---\nRetrieved reference (NVIDIA humanoid baseline and notes; "
        "map behavior into the mandatory SimulationApp script template):\n\n"
        f"{ctx}"
    )


def _simulations_dir() -> Path:
    base = Path(os.getenv("SYNTHERA_DATA_DIR", "~/.synthera-world")).expanduser()
    return base / "simulations"


def _maybe_save_nemotron_humanoid_script(script: str, config: SimConfig, model_name: str) -> None:
    """Mirror humanoid script to a fixed path for local extension demos."""
    if config.robot.category != "humanoid":
        return

    target = Path(
        os.getenv(
            "NEMOTRON_HUMANOID_SCRIPT_PATH",
            "/home/sidg/isaacsim/extension_examples/humanoid/nemotron_humanoid.py",
        )
    ).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(script, encoding="utf-8")


def _normalize_script(text: object) -> str:
    if not isinstance(text, str):
        raise HTTPException(
            status_code=502,
            detail=f"Model returned non-text content type: {type(text).__name__}",
        )

    script = text.strip()
    if not script:
        raise HTTPException(status_code=502, detail="Model returned empty script content.")

    if script.startswith("```"):
        lines = script.splitlines()
        if len(lines) >= 3 and lines[0].startswith("```") and lines[-1].strip() == "```":
            script = "\n".join(lines[1:-1]).strip()
    return script


def _strip_unsupported_environment_paths(script: str) -> str:
    """Drop lines that reference unsupported /Isaac/Environments/ paths."""
    cleaned: list[str] = []
    for line in script.splitlines():
        if "/Isaac/Environments/" in line:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def _fix_import_order(script: str) -> str:
    """Move non-SimulationApp isaacsim imports below SimulationApp initialization."""
    lines = script.splitlines()
    init_idx = None
    for i, line in enumerate(lines):
        if "SimulationApp(" in line:
            init_idx = i
            break
    if init_idx is None:
        return script

    pre = lines[: init_idx + 1]
    post = lines[init_idx + 1 :]
    moved: list[str] = []
    kept_pre: list[str] = []

    for line in pre:
        stripped = line.strip()
        is_isaac_import = stripped.startswith("from isaacsim") or stripped.startswith("import isaacsim")
        is_sim_app_import = "SimulationApp" in line
        if is_isaac_import and not is_sim_app_import:
            moved.append(line)
        else:
            kept_pre.append(line)

    if not moved:
        return script

    return "\n".join(kept_pre + moved + post)


def _normalize_simulation_app_import(script: str) -> str:
    """Normalize common model import variants to required SimulationApp import."""
    script = script.replace(
        "from isaacsim.core.api import SimulationApp, World",
        "from isaacsim import SimulationApp\nfrom isaacsim.core.api import World",
    )
    script = script.replace(
        "from isaacsim.core.api import World, SimulationApp",
        "from isaacsim import SimulationApp\nfrom isaacsim.core.api import World",
    )
    script = script.replace(
        "from isaacsim.core.api import SimulationApp",
        "from isaacsim import SimulationApp",
    )
    return script


def _strip_fake_isaac_helpers(script: str) -> str:
    """Remove common hallucinated helper imports from isaacsim root package."""
    blocked_lines = {
        "from isaacsim import import_asset",
        "from isaacsim import load_asset",
        "from isaacsim import add_reference_to_stage",
        "from isaacsim.robot.wheeled_robots import *",
    }
    cleaned = [line for line in script.splitlines() if line.strip() not in blocked_lines]
    return "\n".join(cleaned)


def _sanitize_script(script: str) -> str:
    """Apply lightweight repairs for common model failures."""
    script = _normalize_simulation_app_import(script)
    script = _strip_fake_isaac_helpers(script)
    script = _strip_unsupported_environment_paths(script)
    script = _fix_import_order(script)
    return script


def _use_h1_stand_template(config: SimConfig) -> bool:
    """Match explicit stand/still tasks only — avoid substring match inside 'standalone'."""
    description = config.task.description.strip().lower()
    return (
        config.robot.category == "humanoid"
        and config.robot.asset_name == "Unitree H1"
        and config.robot.asset_path == "/Isaac/Robots/Unitree/H1/h1.usd"
        and re.search(r"\bstand\b", description) is not None
    )


def _build_h1_stand_script(headless: bool, duration_seconds: int) -> str:
    render = "False" if headless else "True"
    steps = duration_seconds * 60
    return f"""from isaacsim import SimulationApp
simulation_app = SimulationApp({{"headless": {str(headless)}}})

from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()
add_reference_to_stage("/Isaac/Robots/Unitree/H1/h1.usd", "/World/H1")

world.reset()
try:
    for _ in range({steps}):
        world.step(render={render})
except KeyboardInterrupt:
    pass
finally:
    simulation_app.close()
"""


@router.post("/generate", response_model=GenerateResponse)
async def generate_script(config: SimConfig, request: Request) -> GenerateResponse:
    """Generate and persist a script from user simulation config."""
    now = time.monotonic()
    elapsed = now - request.app.state.last_generate_at
    if elapsed < 5:
        raise HTTPException(
            status_code=429,
            detail=f"Generate cooldown active. Retry in {round(5 - elapsed, 1)}s.",
        )

    system_prompt = request.app.state.system_prompt
    engine = request.app.state.db_engine

    if _use_h1_stand_template(config):
        result = {
            "script": _build_h1_stand_script(
                headless=config.output.headless,
                duration_seconds=config.task.duration_seconds,
            ),
            "usage": {"total_tokens": 0},
            "model": "local-template:h1-stand-v1",
        }
    else:
        ai_client = AIClient()
        user_prompt = build_user_prompt(config) + _retrieve_chunks_for_generate(request, config)
        try:
            result = await ai_client.generate_script(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=502, detail=str(exc)) from exc
    request.app.state.last_generate_at = time.monotonic()

    script = _sanitize_script(_normalize_script(result["script"]))
    try:
        validate_script(script)
    except ScriptValidationError as exc:
        raise HTTPException(status_code=400, detail={"validation_errors": exc.errors}) from exc

    generation_id = str(uuid.uuid4())
    sim_dir = _simulations_dir() / generation_id
    sim_dir.mkdir(parents=True, exist_ok=True)

    script_path = sim_dir / "script.py"
    config_path = sim_dir / "config.json"

    script_path.write_text(script, encoding="utf-8")
    config_path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    _maybe_save_nemotron_humanoid_script(script, config, result["model"])

    record = SimulationRecord(
        generation_id=generation_id,
        robot_category=config.robot.category,
        robot_name=config.robot.asset_name,
        task_description=config.task.description,
        config_json=json.dumps(config.model_dump()),
        script_path=str(script_path),
        status="pending",
        tokens_used=result["usage"].get("total_tokens"),
        ai_model=result["model"],
    )

    with Session(engine) as session:
        session.add(record)
        session.commit()

    return GenerateResponse(
        generation_id=generation_id,
        script=script,
        model=result["model"],
        validation_passed=True,
    )
