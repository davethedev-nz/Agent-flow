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


class EfficiencyConfig(BaseModel):
    prefer_minimal_context: bool = True
    max_context_files: int = 12
    max_context_file_bytes: int = 80_000
    max_prompt_chars: int = 24_000
    require_diff_scoped_repair_context: bool = True
    summarize_large_logs: bool = True


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
    efficiency: EfficiencyConfig = Field(default_factory=EfficiencyConfig)


class ResolvedConfig(BaseModel):
    settings: dict[str, ResolvedSetting] = Field(default_factory=dict)
