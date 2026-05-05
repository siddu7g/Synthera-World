"""Script validation service for generated Isaac Sim scripts."""

from __future__ import annotations

import ast
import builtins
import json
import os
from pathlib import Path
from typing import Any


FORBIDDEN = [
    "omni.isaac.",
    "subprocess",
    "os.system",
    "eval(",
    "exec(",
    "__import__",
    "from isaacsim.robot.wheeled_robots import Jackal",
    "from isaacsim import import_asset",
    "from isaacsim import load_asset",
    "from isaacsim import add_reference_to_stage",
    "from isaacsim.robot.wheeled_robots import *",
    "world.scene.set_lighting(",
    "world.load_assembly(",
]
SUPPORTED_ASSET_PATHS = {
    "/Isaac/Robots/Unitree/H1/h1.usd",
    "/Isaac/Robots/Clearpath/Ridgeback/ridgeback.usd",
    "/Isaac/Robots/Clearpath/Jackal/jackal.usd",
    "/Isaac/Robots/Carter/carter_v1.usd",
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
API_REFERENCE_PATH = DATA_DIR / "api_reference.json"
ASSET_CATALOG_PATH = DATA_DIR / "asset_catalog.json"


class ScriptValidationError(Exception):
    """Raised when generated script fails validation."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self.errors = errors
        super().__init__("Script validation failed")


def _load_allowed_assets() -> set[str]:
    if not ASSET_CATALOG_PATH.exists():
        return SUPPORTED_ASSET_PATHS

    data = json.loads(ASSET_CATALOG_PATH.read_text(encoding="utf-8"))
    allowed: set[str] = set()
    for category in ("humanoid", "amr"):
        for item in data.get(category, []):
            path = item.get("asset_path")
            if isinstance(path, str):
                allowed.add(path)
    return allowed or SUPPORTED_ASSET_PATHS


def _load_allowed_modules() -> set[str]:
    if not API_REFERENCE_PATH.exists():
        return {"isaacsim"}
    data = json.loads(API_REFERENCE_PATH.read_text(encoding="utf-8"))
    modules = data.get("allowed_modules", ["isaacsim"])
    return {m for m in modules if isinstance(m, str)}


def _module_allowed(module_name: str, allowed_modules: set[str]) -> bool:
    """Allow exact matches and compatible namespace prefixes."""
    if module_name in allowed_modules:
        return True
    for allowed in allowed_modules:
        if module_name.startswith(f"{allowed}."):
            return True
        # If an allowed module is a deeper path, allow importing its parent namespace.
        if allowed.startswith(f"{module_name}."):
            return True
    return False


def _extract_string_constants(tree: ast.AST) -> list[tuple[int, str]]:
    values: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            values.append((getattr(node, "lineno", 0), node.value))
    return values


def _collect_defined_names(tree: ast.AST) -> set[str]:
    defined: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)
        elif isinstance(node, ast.For):
            if isinstance(node.target, ast.Name):
                defined.add(node.target.id)
        elif isinstance(node, ast.With):
            for item in node.items:
                if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                    defined.add(item.optional_vars.id)
        elif isinstance(node, ast.ExceptHandler):
            if isinstance(node.name, str):
                defined.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined.add(node.name)
            for arg in node.args.args:
                defined.add(arg.arg)
            for arg in node.args.kwonlyargs:
                defined.add(arg.arg)
            if node.args.vararg:
                defined.add(node.args.vararg.arg)
            if node.args.kwarg:
                defined.add(node.args.kwarg.arg)
        elif isinstance(node, ast.ClassDef):
            defined.add(node.name)
    return defined


def _find_undefined_names(tree: ast.AST) -> list[tuple[int, str]]:
    builtins_set = set(dir(builtins))
    defined = _collect_defined_names(tree)
    undefined: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            name = node.id
            if name in defined or name in builtins_set:
                continue
            undefined.append((getattr(node, "lineno", 0), name))
    return undefined


def _humanoid_script_mode() -> str:
    mode = os.getenv("HUMANOID_SCRIPT_MODE", "standalone").strip().lower()
    if mode in {"basesample", "standalone"}:
        return mode
    return "standalone"


def _validate_basesample_structure(script: str, tree: ast.AST, errors: list[dict[str, Any]]) -> None:
    """Validate humanoid BaseSample extension structure."""
    if "from isaacsim import SimulationApp" in script or "SimulationApp(" in script:
        errors.append(
            {
                "layer": "api_surface",
                "line": 0,
                "message": "BaseSample mode forbids standalone SimulationApp initialization.",
            }
        )
    if "simulation_app.close()" in script:
        errors.append(
            {
                "layer": "api_surface",
                "line": 0,
                "message": "BaseSample mode forbids simulation_app.close().",
            }
        )

    humanoid_class: ast.ClassDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "HumanoidExample":
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "BaseSample":
                    humanoid_class = node
                    break

    if humanoid_class is None:
        errors.append(
            {
                "layer": "api_surface",
                "line": 0,
                "message": "BaseSample mode requires class HumanoidExample(BaseSample).",
            }
        )
        return

    required_methods = {
        "__init__",
        "setup_scene",
        "setup_post_load",
        "setup_post_reset",
        "on_physics_step",
        "_timeline_timer_callback_fn",
        "world_cleanup",
    }
    methods = {n.name for n in humanoid_class.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for method in sorted(required_methods - methods):
        errors.append(
            {
                "layer": "api_surface",
                "line": humanoid_class.lineno,
                "message": f"BaseSample mode missing required method: {method}",
            }
        )


def validate_script(script: str) -> None:
    """Validate generated script with 5-layer checks."""
    errors: list[dict[str, Any]] = []

    # Layer 1: Syntax
    try:
        tree = ast.parse(script)
    except SyntaxError as exc:
        errors.append(
            {
                "layer": "syntax",
                "line": exc.lineno or 0,
                "message": exc.msg,
            }
        )
        raise ScriptValidationError(errors)

    # Layer 2: Forbidden patterns
    for forbidden in FORBIDDEN:
        if forbidden in script:
            errors.append(
                {
                    "layer": "forbidden_pattern",
                    "line": 0,
                    "message": f"Forbidden pattern detected: {forbidden}",
                }
            )

    # Layer 3: API surface
    allowed_modules = _load_allowed_modules()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("isaacsim") and not _module_allowed(node.module, allowed_modules):
                errors.append(
                    {
                        "layer": "api_surface",
                        "line": node.lineno,
                        "message": f"Module not in allowed API surface: {node.module}",
                    }
                )
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("isaacsim") and not _module_allowed(alias.name, allowed_modules):
                    errors.append(
                        {
                            "layer": "api_surface",
                            "line": node.lineno,
                            "message": f"Module not in allowed API surface: {alias.name}",
                        }
                    )

    # Layer 3b: Undefined symbols (common model hallucinations)
    undefined_names = _find_undefined_names(tree)
    ignored = {"simulation_app", "world"}
    for lineno, name in undefined_names:
        if name in ignored:
            continue
        errors.append(
            {
                "layer": "api_surface",
                "line": lineno,
                "message": f"Undefined symbol likely hallucinated: {name}",
            }
        )

    # Additional structural checks for beta reliability
    humanoid_mode = _humanoid_script_mode()
    if humanoid_mode == "basesample":
        _validate_basesample_structure(script, tree, errors)
    else:
        has_sim_app_import = False
        has_world_import = False
        has_world_init = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "isaacsim":
                imported = {alias.name for alias in node.names}
                if "SimulationApp" in imported:
                    has_sim_app_import = True
            if isinstance(node, ast.ImportFrom) and node.module == "isaacsim.core.api":
                imported = {alias.name for alias in node.names}
                if "World" in imported:
                    has_world_import = True
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name) and func.id == "World":
                    has_world_init = True

        if not has_sim_app_import:
            errors.append(
                {
                    "layer": "api_surface",
                    "line": 0,
                    "message": "Missing required import: from isaacsim import SimulationApp",
                }
            )

        if not has_world_import:
            errors.append(
                {
                    "layer": "api_surface",
                    "line": 0,
                    "message": "Missing required import: from isaacsim.core.api import World",
                }
            )

        if not has_world_init:
            errors.append(
                {
                    "layer": "api_surface",
                    "line": 0,
                    "message": "Missing world initialization: world = World(...)",
                }
            )

    # Layer 4: Asset paths
    allowed_assets = _load_allowed_assets()
    for lineno, text in _extract_string_constants(tree):
        if "/Isaac/" in text and text not in allowed_assets:
            errors.append(
                {
                    "layer": "asset_path",
                    "line": lineno,
                    "message": f"Asset path is not in catalog: {text}",
                }
            )

    # Layer 5: Import order (standalone mode only)
    if humanoid_mode != "basesample":
        lines = script.splitlines()
        simulation_app_init_line = 0
        simulation_app_import_line = 0
        simulation_app_module_import_line = 0
        isaacsim_import_lines: list[int] = []
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("from isaacsim import SimulationApp"):
                simulation_app_import_line = idx
            if stripped.startswith("import isaacsim"):
                simulation_app_module_import_line = idx
            if "SimulationApp(" in line and simulation_app_init_line == 0:
                simulation_app_init_line = idx
            if stripped.startswith("from isaacsim") or stripped.startswith("import isaacsim"):
                isaacsim_import_lines.append(idx)

        if simulation_app_init_line == 0:
            errors.append(
                {
                    "layer": "import_order",
                    "line": 0,
                    "message": "SimulationApp was not initialized.",
                }
            )
        elif simulation_app_import_line == 0 and simulation_app_module_import_line == 0:
            errors.append(
                {
                    "layer": "import_order",
                    "line": 0,
                    "message": (
                        "Missing SimulationApp import. Use either "
                        "'from isaacsim import SimulationApp' or 'import isaacsim'."
                    ),
                }
            )
        else:
            for line_no in isaacsim_import_lines:
                if line_no > simulation_app_init_line:
                    continue
                if line_no == simulation_app_import_line:
                    continue
                if line_no == simulation_app_module_import_line:
                    continue
                if "SimulationApp" not in lines[line_no - 1]:
                    errors.append(
                        {
                            "layer": "import_order",
                            "line": line_no,
                            "message": "isaacsim import appears before SimulationApp initialization.",
                        }
                    )

    if errors:
        raise ScriptValidationError(errors)
