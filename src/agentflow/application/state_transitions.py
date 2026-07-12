from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from agentflow.domain.enums import TaskState
from agentflow.domain.task_records import TaskRecord, TaskStateSnapshot, TaskStatusResult, TaskTransitionResult
from agentflow.infrastructure.git_worktrees import GitWorktreeService
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery
from agentflow.application.task_records import TaskRecordService
from agentflow.application.task_events import TaskEventService


class TaskTransitionService:
    _allowed: dict[TaskState, set[TaskState]] = {
        TaskState.CREATED: {TaskState.PLANNING, TaskState.BLOCKED, TaskState.CANCELLED},
        TaskState.PLANNING: {TaskState.PLAN_REVIEW, TaskState.BLOCKED, TaskState.CANCELLED},
        TaskState.PLAN_REVIEW: {TaskState.PLANNING, TaskState.IMPLEMENTING, TaskState.BLOCKED, TaskState.CANCELLED},
        TaskState.IMPLEMENTING: {TaskState.VALIDATING, TaskState.BLOCKED},
        TaskState.VALIDATING: {TaskState.CODE_REVIEW, TaskState.REPAIRING, TaskState.BLOCKED},
        TaskState.REPAIRING: {TaskState.VALIDATING, TaskState.BLOCKED},
        TaskState.CODE_REVIEW: {TaskState.REPAIRING, TaskState.DOCUMENTING, TaskState.FINAL_REVIEW, TaskState.BLOCKED},
        TaskState.DOCUMENTING: {TaskState.FINAL_REVIEW, TaskState.BLOCKED},
        TaskState.FINAL_REVIEW: {TaskState.DOCUMENTING, TaskState.READY_TO_COMMIT, TaskState.BLOCKED},
        TaskState.READY_TO_COMMIT: {TaskState.COMPLETE, TaskState.BLOCKED},
        TaskState.COMPLETE: set(),
        TaskState.BLOCKED: {TaskState.PLANNING, TaskState.IMPLEMENTING, TaskState.CANCELLED},
        TaskState.CANCELLED: set(),
    }

    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._events = TaskEventService(discovery)
        self._worktrees = GitWorktreeService(discovery)

    def status(self, path: Path, task_id: str) -> TaskStatusResult:
        task, state = self._load(path, task_id)
        worktree = self._records.load_worktree(path, task_id)
        return TaskStatusResult(
            task_id=task.task_id,
            title=task.title,
            current_state=state.current_state,
            previous_state=state.previous_state,
            updated_at=state.updated_at,
            transition_reason=state.transition_reason,
            allowed_transitions=sorted(self._allowed[state.current_state], key=lambda item: item.value),
            worktree_path=worktree.path if worktree else None,
        )

    def transition(
        self,
        path: Path,
        task_id: str,
        target_state: TaskState,
        reason: str | None = None,
        event_type: str = "task_state_changed",
        ensure_worktree: bool = False,
    ) -> TaskTransitionResult:
        task, state = self._load(path, task_id)
        previous_state = state.current_state
        if target_state not in self._allowed[previous_state]:
            raise ValueError(f"Transition from {previous_state.value} to {target_state.value} is not allowed.")

        updated_at = datetime.now(UTC).isoformat()
        task.current_state = target_state
        state.previous_state = previous_state
        state.current_state = target_state
        state.updated_at = updated_at
        state.transition_reason = reason

        task_root = self._records.task_root(path, task_id)
        self._records.write_task_record(task_root / "task.yaml", task)
        self._records.write_state_snapshot(task_root / "state.json", state)
        if ensure_worktree:
            self._worktrees.ensure_task_worktree(path, task_id)
        self._events.append(
            path,
            task_id,
            event_type=event_type,
            previous_state=previous_state.value,
            resulting_state=target_state.value,
            payload={"reason": reason} if reason else {},
        )

        return TaskTransitionResult(
            task_id=task_id,
            previous_state=previous_state,
            current_state=target_state,
            updated_at=updated_at,
            transition_reason=reason,
        )

    def _load(self, path: Path, task_id: str) -> tuple[TaskRecord, TaskStateSnapshot]:
        task = self._records.show(path, task_id)
        state = self._records.load_state(path, task_id)
        return task, state