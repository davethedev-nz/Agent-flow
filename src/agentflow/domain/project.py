from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ProjectInspection(BaseModel):
    requested_path: Path
    repository_root: Path | None
    is_git_repository: bool
    agentflow_initialized: bool
    stack_hints: list[str] = Field(default_factory=list)


class DoctorCheck(BaseModel):
    name: str
    status: str
    details: str


class DoctorReport(BaseModel):
    requested_path: Path
    repository_root: Path | None
    checks: list[DoctorCheck] = Field(default_factory=list)