from __future__ import annotations

from pydantic import BaseModel, Field


class PendingCommandApproval(BaseModel):
    task_id: str
    command: list[str] = Field(default_factory=list)
    reason: str


class CommandExecutionResult(BaseModel):
    task_id: str
    command: list[str] = Field(default_factory=list)
    exit_code: int
    stdout: str
    stderr: str
    approval_required: bool = False
    approval_reason: str | None = None
