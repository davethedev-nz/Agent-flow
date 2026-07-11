from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from agentflow.application.state_transitions import TaskTransitionService
from agentflow.application.task_events import TaskEventService
from agentflow.application.task_records import TaskRecordService
from agentflow.domain.enums import TaskState
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class FinalizationService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._events = TaskEventService(discovery)
        self._transitions = TaskTransitionService(discovery)

    def approve_and_commit(self, path: Path, task_id: str, message: str | None = None) -> dict[str, object]:
        state = self._records.load_state(path, task_id).current_state
        if state not in {TaskState.FINAL_REVIEW, TaskState.READY_TO_COMMIT}:
            raise ValueError(f"approve-commit is only allowed from final_review or ready_to_commit, not {state.value}.")

        if state == TaskState.FINAL_REVIEW:
            self._transitions.transition(
                path,
                task_id,
                TaskState.READY_TO_COMMIT,
                reason="Final approval granted",
                event_type="final_approval_granted",
            )

        task_root = self._records.task_root(path, task_id)
        task = self._records.show(path, task_id)
        worktree = self._records.load_worktree(path, task_id)
        working_directory = Path(worktree.path) if worktree else task.repository_root
        commit_message = message or f"agentflow: complete {task_id}"

        self._run(["git", "add", "-A"], working_directory)
        has_staged_changes = self._run_optional(["git", "diff", "--cached", "--quiet"], working_directory) is False
        if not has_staged_changes:
            raise ValueError("No staged changes are available for commit.")

        self._run(["git", "commit", "-m", commit_message], working_directory)
        commit_sha = self._run(["git", "rev-parse", "HEAD"], working_directory).strip()

        completion_payload = {
            "task_id": task_id,
            "commit": commit_sha,
            "message": commit_message,
            "completed_at": datetime.now(UTC).isoformat(),
        }
        self._records.write_text(task_root / "completion.json", json.dumps(completion_payload, indent=2) + "\n")
        self._events.append(path, task_id, "commit_created", None, None, payload={"commit": commit_sha})
        self._transitions.transition(
            path,
            task_id,
            TaskState.COMPLETE,
            reason="Local commit created",
            event_type="task_completed",
        )
        return completion_payload

    def _run(self, argv: list[str], cwd: Path) -> str:
        completed = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise ValueError((completed.stderr or completed.stdout).strip() or f"Command failed: {' '.join(argv)}")
        return completed.stdout

    def _run_optional(self, argv: list[str], cwd: Path) -> bool:
        completed = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=False)
        return completed.returncode == 0