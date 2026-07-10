from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ResolvedSetting(BaseModel):
    value: object
    origin: str


class AutonomyConfig(BaseModel):
    plan_requires_approval: bool = True
    code_edits_require_approval: bool = False
    scope_expansion_requires_approval: bool = True
    command_approval_mode: str = "allowlist"
    maximum_repair_iterations: int = 4
    commit_requires_approval: bool = True
    push_allowed: bool = False


class ProjectConfig(BaseModel):
    project_id: str
    repository_root: Path
    source_paths: list[str] = Field(default_factory=list)
    test_paths: list[str] = Field(default_factory=list)
    documentation_paths: list[str] = Field(default_factory=list)
    infrastructure_paths: list[str] = Field(default_factory=list)
    forbidden_paths: list[str] = Field(default_factory=list)
    validation_commands: list[list[str]] = Field(default_factory=list)
    autonomy: AutonomyConfig = Field(default_factory=AutonomyConfig)


class ResolvedConfig(BaseModel):
    settings: dict[str, ResolvedSetting] = Field(default_factory=dict)
