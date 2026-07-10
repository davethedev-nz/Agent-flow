from __future__ import annotations

from pydantic import BaseModel, Field


class TaskEvent(BaseModel):
    schema_version: int = 1
    event_id: str
    task_id: str
    event_type: str
    timestamp: str
    actor: str = "agentflow"
    previous_state: str | None = None
    resulting_state: str | None = None
    correlation_id: str
    causation_id: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)
    related_run_id: str | None = None
