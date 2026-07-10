from __future__ import annotations

from pydantic import BaseModel, Field


class ValidatorDefinition(BaseModel):
    validator_id: str
    description: str
    command: list[str]
    timeout_seconds: int = 600
    depends_on: list[str] = Field(default_factory=list)
    continue_on_failure: bool = False


class ValidationPipelineDefinition(BaseModel):
    validators: list[ValidatorDefinition] = Field(default_factory=list)
