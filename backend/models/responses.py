"""Response schemas for API routes."""

from pydantic import BaseModel


class GenerateResponse(BaseModel):
    generation_id: str
    script: str
    model: str
    validation_passed: bool
