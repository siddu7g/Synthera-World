"""FastAPI entrypoint for Synthera World backend."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models.database import init_database
from routers.assets import router as assets_router
from routers.chat import router as chat_router
from routers.generate import router as generate_router
from routers.history import router as history_router
from routers.simulate import router as simulate_router
from services.isaac_runner import IsaacRunner
from services.prompt_builder import build_system_prompt
from services.rag_service import RagService


def _load_env() -> None:
    """Load environment variables from project and backend .env files."""
    backend_dir = Path(__file__).resolve().parent
    project_root = backend_dir.parent
    load_dotenv(project_root / ".env", override=False)
    load_dotenv(backend_dir / ".env", override=False)


def _ensure_app_dirs() -> None:
    data_dir = Path(os.getenv("SYNTHERA_DATA_DIR", "~/.synthera-world")).expanduser()
    (data_dir / "simulations").mkdir(parents=True, exist_ok=True)


app = FastAPI(title="Synthera World API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize database and prompt cache."""
    _load_env()
    _ensure_app_dirs()
    app.state.db_engine = init_database()
    app.state.system_prompt = build_system_prompt()
    app.state.isaac_runner = IsaacRunner()
    app.state.last_generate_at = 0.0
    app.state.chat_sessions = {}
    rag = RagService(docs_dir=os.getenv("RAG_DOCS_DIR", "../rag"))
    rag.load()
    app.state.rag_service = rag


@app.get("/health")
async def health() -> dict[str, str]:
    """Return API, runtime env, and key status."""
    isaac_path = Path(os.getenv("ISAAC_SIM_PATH", "")).expanduser()
    api_key_set = bool(os.getenv("OPENROUTER_API_KEY"))
    return {
        "status": "ok",
        "isaac_path_exists": str(isaac_path.exists()),
        "openrouter_key_set": str(api_key_set),
        "ai_model": os.getenv("AI_MODEL", ""),
        "ai_fallback_model": os.getenv("AI_FALLBACK_MODEL", ""),
    }


app.include_router(generate_router)
app.include_router(simulate_router)
app.include_router(assets_router)
app.include_router(history_router)
app.include_router(chat_router)
