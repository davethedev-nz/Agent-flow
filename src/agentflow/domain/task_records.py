from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class TaskRecord(BaseModel):
    schema_version: int = 1
    task_id: str
    title: str
    current_state: str = "created"
    repository_root: Path
    created_at: str


class TaskStateSnapshot(BaseModel):
    schema_version: int = 1
    task_id: str
    current_state: str = "created"
    updated_at: str


class TaskRecordSummary(BaseModel):
    task_id: str
    title: str
    current_state: str


class TaskCreateResult(BaseModel):
    task: TaskRecord
    created_files: list[str] = Field(default_factory=list)
