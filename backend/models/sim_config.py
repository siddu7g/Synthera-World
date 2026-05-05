"""Pydantic schema for simulation configuration."""

from typing import Literal

from pydantic import BaseModel, Field


class RobotConfig(BaseModel):
    category: Literal["humanoid", "amr"]
    asset_name: str = Field(min_length=1, max_length=200)
    asset_path: str = Field(min_length=1, max_length=500)


class SceneConfig(BaseModel):
    environment: Literal["warehouse", "empty", "outdoor_terrain"]
    lighting: Literal["day", "artificial", "night"]
    obstacles: bool


class TaskConfig(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    duration_seconds: int = Field(ge=10, le=120)


class SensorsConfig(BaseModel):
    camera: bool
    imu: bool
    lidar: bool


class OutputConfig(BaseModel):
    headless: bool = True
    export_telemetry: bool = False


class SimConfig(BaseModel):
    robot: RobotConfig
    scene: SceneConfig
    task: TaskConfig
    sensors: SensorsConfig
    output: OutputConfig
