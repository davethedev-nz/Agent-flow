from __future__ import annotations

from agentflow.application.protocols import EventRepository, TaskRepository
from agentflow.domain.models import TaskDefinition


class TaskService:
    """Thin application facade for early implementation slices."""

    def __init__(self, tasks: TaskRepository, events: EventRepository) -> None:
        self._tasks = tasks
        self._events = events

    def create_task(self, task: TaskDefinition) -> None:
        self._tasks.create(task)
        self._events.append(
            "task_created",
            {
                "task_id": task.reference.task_id,
                "state": task.current_state.value,
                "title": task.title,
            },
        )
