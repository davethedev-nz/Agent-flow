from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from agentflow.domain.enums import TaskState


class TaskRecord(BaseModel):
    schema_version: int = 1
    task_id: str
    title: str
    current_state: TaskState = TaskState.CREATED
    repository_root: Path
    created_at: str


class TaskStateSnapshot(BaseModel):
    schema_version: int = 1
    task_id: str
    current_state: TaskState = TaskState.CREATED
    previous_state: TaskState | None = None
    updated_at: str
    transition_reason: str | None = None


class TaskRecordSummary(BaseModel):
    task_id: str
    title: str
    current_state: TaskState


class TaskCreateResult(BaseModel):
    task: TaskRecord
    created_files: list[str] = Field(default_factory=list)


class TaskStatusResult(BaseModel):
    task_id: str
    title: str
    current_state: TaskState
    previous_state: TaskState | None = None
    updated_at: str
    transition_reason: str | None = None
    allowed_transitions: list[TaskState] = Field(default_factory=list)


class TaskTransitionResult(BaseModel):
    task_id: str
    previous_state: TaskState
    current_state: TaskState
    updated_at: str
    transition_reason: str | None = None
