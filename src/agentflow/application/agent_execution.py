from __future__ import annotations

import json
import uuid
from pathlib import Path

from agentflow.adapters.fake import FakeAgentAdapter
from agentflow.adapters.subprocess_text import SubprocessTextAgentAdapter
from agentflow.application.path_policy import PathPolicyViolationError, RepositoryPathPolicy
from agentflow.application.state_transitions import TaskTransitionService
from agentflow.application.task_events import TaskEventService
from agentflow.application.task_records import TaskRecordService
from agentflow.domain.enums import AgentRole
from agentflow.domain.enums import TaskState
from agentflow.domain.models import AgentRequest, AgentResult
from agentflow.infrastructure.git_changes import GitChangedFileService
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class AgentExecutionService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._events = TaskEventService(discovery)
        self._transitions = TaskTransitionService(discovery)
        self._changes = GitChangedFileService()

    def run(
        self,
        path: Path,
        task_id: str,
        role: AgentRole,
        prompt: str,
        adapter_name: str,
        command: list[str] | None = None,
    ) -> AgentResult:
        task_root = self._records.task_root(path, task_id)
        task = self._records.show(path, task_id)
        worktree = self._records.load_worktree(path, task_id)
        working_directory = Path(worktree.path) if worktree else task.repository_root
        path_policy = RepositoryPathPolicy(task.repository_root, role)
        request = AgentRequest(
            task_id=task_id,
            role=role,
            prompt=prompt,
            working_directory=working_directory,
            repository_root=task.repository_root,
            allowed_paths=path_policy.editable_paths,
            forbidden_paths=path_policy.forbidden_paths,
            expected_output_schema="generic",
        )

        before_changed_files = self._changes.list_changed_files(working_directory)
        adapter = self._adapter(adapter_name, command)
        result = adapter.execute(request)
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        runs_root = task_root / "runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        result_path = runs_root / f"{run_id}.json"
        result_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
        result.raw_output_location = result_path

        changed_files = [
            changed_path
            for changed_path in self._changes.list_changed_files(working_directory)
            if changed_path not in before_changed_files and not self._is_system_artifact(changed_path, task_id)
        ]
        result.changed_files = changed_files

        violations = path_policy.validate_changes(changed_files)
        if violations:
            reason = "Path policy violation: " + "; ".join(violations)
            self._records.write_text(
                task_root / "policy-violations.json",
                json.dumps({"violations": violations, "changed_files": [str(file_path) for file_path in changed_files]}, indent=2)
                + "\n",
            )
            self._events.append(
                path,
                task_id,
                "file_scope_violation_detected",
                None,
                None,
                payload={"changed_files": [str(file_path) for file_path in changed_files], "violations": violations},
            )
            try:
                self._transitions.transition(path, task_id, TaskState.BLOCKED, reason=reason, event_type="task_blocked")
            except ValueError:
                pass
            raise PathPolicyViolationError(violations)

        if task.current_state == TaskState.IMPLEMENTING:
            self._transitions.transition(
                path,
                task_id,
                TaskState.VALIDATING,
                reason="Agent run completed",
                event_type="agent_completed",
            )
        return result

    def _is_system_artifact(self, changed_path: Path, task_id: str) -> bool:
        normalized = changed_path.as_posix()
        while normalized.startswith("./"):
            normalized = normalized[2:]
        if normalized == ".agentflow/tmp-subprocess-output.txt":
            return True
        task_prefix = f".agentflow/tasks/{task_id}/"
        if not normalized.startswith(task_prefix):
            return False

        relative = normalized[len(task_prefix) :]
        return relative.startswith("runs/") or relative == "policy-violations.json"

    def _adapter(self, adapter_name: str, command: list[str] | None) -> FakeAgentAdapter | SubprocessTextAgentAdapter:
        if adapter_name == "fake":
            return FakeAgentAdapter()
        if adapter_name == "subprocess-text":
            return SubprocessTextAgentAdapter(command or [])
        raise ValueError(f"Unsupported adapter {adapter_name}.")
