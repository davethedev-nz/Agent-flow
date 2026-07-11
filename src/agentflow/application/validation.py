from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

from agentflow.application.state_transitions import TaskTransitionService
from agentflow.application.task_events import TaskEventService
from agentflow.application.task_records import TaskRecordService
from agentflow.domain.enums import TaskState
from agentflow.domain.models import ValidationResult
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery
from agentflow.validation.models import ValidationPipelineDefinition


class ValidationService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._events = TaskEventService(discovery)
        self._transitions = TaskTransitionService(discovery)

    def run_for_task(self, path: Path, task_id: str) -> list[ValidationResult]:
        task_root = self._records.task_root(path, task_id)
        state = self._records.load_state(path, task_id)
        worktree = self._records.load_worktree(path, task_id)
        working_directory = Path(worktree.path) if worktree else self._records.show(path, task_id).repository_root

        if state.current_state == TaskState.IMPLEMENTING:
            self._transitions.transition(
                path,
                task_id,
                TaskState.VALIDATING,
                reason="Validation requested",
                event_type="validation_started",
            )

        pipeline = self._load_pipeline(path, task_id)
        validation_root = task_root / "validation"
        validation_root.mkdir(parents=True, exist_ok=True)
        results: list[ValidationResult] = []

        for validator in pipeline.validators:
            command = validator.command
            stdout = ""
            stderr = ""
            status = "passed"
            try:
                completed = subprocess.run(
                    command,
                    cwd=working_directory,
                    capture_output=True,
                    text=True,
                    timeout=validator.timeout_seconds,
                    check=False,
                )
                stdout = completed.stdout
                stderr = completed.stderr
                status = "passed" if completed.returncode == 0 else "failed"
                exit_code = completed.returncode
            except subprocess.TimeoutExpired as timeout_error:
                stdout = timeout_error.stdout or ""
                stderr = timeout_error.stderr or ""
                status = "timeout"
                exit_code = -1

            log_path = validation_root / f"{validator.validator_id}.log"
            log_path.write_text(
                "\n".join(
                    [
                        f"$ {' '.join(command)}",
                        "",
                        "[stdout]",
                        stdout,
                        "",
                        "[stderr]",
                        stderr,
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = ValidationResult(
                validator_id=validator.validator_id,
                status=status,
                summary=f"{' '.join(command)} -> {status}",
                raw_log_path=log_path,
                metrics={"exit_code": exit_code, "timeout_seconds": validator.timeout_seconds},
            )
            results.append(result)
            self._events.append(
                path,
                task_id,
                "validator_completed",
                None,
                None,
                payload={
                    "validator_id": validator.validator_id,
                    "status": status,
                    "command": command,
                    "exit_code": exit_code,
                },
            )

        self._records.write_text(
            task_root / "validation-results.json",
            json.dumps([item.model_dump(mode="json") for item in results], indent=2) + "\n",
        )

        has_failure = any(item.status != "passed" for item in results)
        current_state = self._records.load_state(path, task_id).current_state
        if has_failure and current_state == TaskState.VALIDATING:
            self._transitions.transition(
                path,
                task_id,
                TaskState.REPAIRING,
                reason="Validation failed",
                event_type="validation_failed",
            )
        elif not has_failure and current_state == TaskState.VALIDATING:
            self._transitions.transition(
                path,
                task_id,
                TaskState.CODE_REVIEW,
                reason="Validation passed",
                event_type="validation_passed",
            )

        return results

    def _load_pipeline(self, path: Path, task_id: str) -> ValidationPipelineDefinition:
        task = self._records.show(path, task_id)
        pipeline_path = task.repository_root / ".agentflow" / "validation.yaml"
        loaded = yaml.safe_load(pipeline_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"Validation pipeline {pipeline_path} must contain a mapping.")
        return ValidationPipelineDefinition.model_validate(loaded)