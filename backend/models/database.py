"""Database models and setup for Synthera World."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlmodel import Field, SQLModel, create_engine


DEFAULT_MODEL = "anthropic/claude-haiku-4-5-20251001"


def get_data_dir() -> Path:
    """Return the configured data directory path."""
    raw = os.getenv("SYNTHERA_DATA_DIR", "~/.synthera-world")
    return Path(raw).expanduser()


def get_db_path() -> Path:
    """Return the SQLite database path."""
    return get_data_dir() / "synthera.db"


class SimulationRecord(SQLModel, table=True):
    generation_id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    robot_category: str
    robot_name: str
    task_description: str
    config_json: str
    script_path: str
    status: str = "pending"
    duration_s: Optional[float] = None
    exit_code: Optional[int] = None
    telemetry_path: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    ai_model: str = DEFAULT_MODEL


def init_database():
    """Initialize SQLite database and return SQLModel engine."""
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{get_db_path()}", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine
