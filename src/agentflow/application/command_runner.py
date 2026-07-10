from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

from agentflow.application.task_events import TaskEventService
from agentflow.application.task_records import TaskRecordService
from agentflow.domain.commands import CommandExecutionResult, PendingCommandApproval
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class RestrictedCommandRunnerService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._events = TaskEventService(discovery)

    def run(self, path: Path, task_id: str, command: list[str]) -> CommandExecutionResult:
        task = self._records.show(path, task_id)
        task_root = self._records.task_root(path, task_id)
        policy = self._load_policy(task.repository_root)

        executable = command[0] if command else ""
        joined = " ".join(command)
        if executable not in policy["allowed_executables"] or any(pattern in joined for pattern in policy["blocked_patterns"]):
            reason = "Command requires approval because it is blocked or not on the allowlist."
            pending = PendingCommandApproval(task_id=task_id, command=command, reason=reason)
            self._records.write_text(task_root / "command-approval.json", json.dumps(pending.model_dump(mode="json"), indent=2) + "\n")
            self._events.append(path, task_id, "command_requested", None, None, payload={"command": command, "reason": reason})
            return CommandExecutionResult(
                task_id=task_id,
                command=command,
                exit_code=1,
                stdout="",
                stderr="",
                approval_required=True,
                approval_reason=reason,
            )

        return self._execute(path, task_id, command)

    def approve(self, path: Path, task_id: str) -> CommandExecutionResult:
        pending = self._load_pending(path, task_id)
        result = self._execute(path, task_id, pending.command)
        self._records.write_text(self._records.task_root(path, task_id) / "command-approval.json", "")
        self._events.append(path, task_id, "command_approved", None, None, payload={"command": pending.command})
        return result

    def reject(self, path: Path, task_id: str) -> None:
        pending = self._load_pending(path, task_id)
        self._records.write_text(self._records.task_root(path, task_id) / "command-approval.json", "")
        self._events.append(path, task_id, "command_rejected", None, None, payload={"command": pending.command})

    def _execute(self, path: Path, task_id: str, command: list[str]) -> CommandExecutionResult:
        task = self._records.show(path, task_id)
        completed = subprocess.run(command, cwd=task.repository_root, capture_output=True, text=True, check=False)
        result = CommandExecutionResult(
            task_id=task_id,
            command=command,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        task_root = self._records.task_root(path, task_id)
        self._records.write_text(task_root / "command-result.json", json.dumps(result.model_dump(mode="json"), indent=2) + "\n")
        self._events.append(path, task_id, "command_executed", None, None, payload={"command": command, "exit_code": completed.returncode})
        return result

    def _load_policy(self, repository_root: Path) -> dict[str, list[str]]:
        policy_path = repository_root / ".agentflow" / "policies" / "commands.yaml"
        loaded = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"Command policy {policy_path} must contain a mapping.")
        return {
            "allowed_executables": list(loaded.get("allowed_executables", [])),
            "blocked_patterns": list(loaded.get("blocked_patterns", [])),
        }

    def _load_pending(self, path: Path, task_id: str) -> PendingCommandApproval:
        task_root = self._records.task_root(path, task_id)
        pending_path = task_root / "command-approval.json"
        if not pending_path.exists() or not pending_path.read_text(encoding="utf-8").strip():
            raise ValueError(f"No pending command approval exists for task {task_id}.")
        loaded = json.loads(pending_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"Pending approval {pending_path} must contain an object.")
        return PendingCommandApproval.model_validate(loaded)
