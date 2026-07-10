from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from agentflow.domain.events import TaskEvent
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class TaskEventService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._discovery = discovery

    def append(
        self,
        path: Path,
        task_id: str,
        event_type: str,
        previous_state: str | None,
        resulting_state: str | None,
        payload: dict[str, object] | None = None,
        causation_id: str | None = None,
    ) -> TaskEvent:
        task_root = self._task_root(path, task_id)
        event = TaskEvent(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            task_id=task_id,
            event_type=event_type,
            timestamp=datetime.now(UTC).isoformat(),
            previous_state=previous_state,
            resulting_state=resulting_state,
            correlation_id=f"corr_{uuid.uuid4().hex[:12]}",
            causation_id=causation_id,
            payload=payload or {},
        )
        self._append_jsonl(task_root / "events.jsonl", event)
        return event

    def list_events(self, path: Path, task_id: str) -> list[TaskEvent]:
        task_root = self._task_root(path, task_id)
        events_path = task_root / "events.jsonl"
        if not events_path.exists():
            return []
        events: list[TaskEvent] = []
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            events.append(TaskEvent.model_validate(json.loads(line)))
        return events

    def _append_jsonl(self, target_path: Path, event: TaskEvent) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json")) + "\n")

    def _task_root(self, path: Path, task_id: str) -> Path:
        inspection = self._discovery.inspect(path)
        if inspection.repository_root is None:
            raise ValueError("Current path is not inside a Git repository.")
        task_root = inspection.repository_root / ".agentflow" / "tasks" / task_id
        if not task_root.exists():
            raise ValueError(f"Task {task_id} was not found.")
        return task_root
