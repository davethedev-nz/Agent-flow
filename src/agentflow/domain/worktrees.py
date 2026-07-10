from __future__ import annotations

from pydantic import BaseModel


class WorktreeRecord(BaseModel):
    task_id: str
    branch: str
    path: str
    head: str
