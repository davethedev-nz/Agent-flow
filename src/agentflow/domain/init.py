from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ProposedPaths(BaseModel):
    source: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    documentation: list[str] = Field(default_factory=list)
    infrastructure: list[str] = Field(default_factory=list)
    forbidden: list[str] = Field(default_factory=list)


class InitFileStatus(BaseModel):
    relative_path: str
    status: str


class InitProposal(BaseModel):
    requested_path: Path
    repository_root: Path | None
    is_git_repository: bool
    agentflow_initialized: bool
    selected_profile: str | None
    stack_hints: list[str] = Field(default_factory=list)
    project_id: str | None = None
    proposed_paths: ProposedPaths = Field(default_factory=ProposedPaths)
    validation_commands: list[list[str]] = Field(default_factory=list)
    files: list[InitFileStatus] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    can_write: bool = False


class InitApplyResult(BaseModel):
    repository_root: Path
    written_files: list[str] = Field(default_factory=list)
    unchanged_files: list[str] = Field(default_factory=list)
    conflict_files: list[str] = Field(default_factory=list)
