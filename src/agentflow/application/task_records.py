from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import yaml

from agentflow.domain.task_records import TaskCreateResult, TaskRecord, TaskRecordSummary, TaskStateSnapshot
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class TaskRecordService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._discovery = discovery

    def create(self, path: Path, task_id: str, title: str | None = None) -> TaskCreateResult:
        repository_root = self._repository_root(path)
        tasks_root = self._tasks_root(repository_root)
        task_root = tasks_root / task_id
        if task_root.exists():
            raise ValueError(f"Task {task_id} already exists.")

        task_root.mkdir(parents=True)
        task = TaskRecord(
            task_id=task_id,
            title=title or task_id,
            repository_root=repository_root,
            created_at=datetime.now(UTC).isoformat(),
        )
        state = TaskStateSnapshot(
            task_id=task_id,
            current_state=task.current_state,
            updated_at=task.created_at,
        )

        created_files = [
            self._write(task_root / "task.yaml", yaml.safe_dump(task.model_dump(mode="json"), sort_keys=False)),
            self._write(task_root / "requirements.md", "# Requirements\n\nDescribe the user story and constraints here.\n"),
            self._write(
                task_root / "acceptance-criteria.md",
                "# Acceptance Criteria\n\n- Define the observable outcomes that must pass before approval.\n",
            ),
            self._write(task_root / "plan.md", "# Plan\n\nPlan generation has not started yet.\n"),
            self._write(task_root / "state.json", self._json_dump(state.model_dump(mode="json"))),
        ]

        return TaskCreateResult(task=task, created_files=created_files)

    def list_tasks(self, path: Path) -> list[TaskRecordSummary]:
        repository_root = self._repository_root(path)
        tasks_root = self._tasks_root(repository_root)
        summaries: list[TaskRecordSummary] = []
        for task_dir in sorted(tasks_root.iterdir()):
            if not task_dir.is_dir():
                continue
            task_file = task_dir / "task.yaml"
            if not task_file.exists():
                continue
            task = self._load_task(task_file)
            summaries.append(
                TaskRecordSummary(
                    task_id=task.task_id,
                    title=task.title,
                    current_state=task.current_state,
                )
            )
        return summaries

    def show(self, path: Path, task_id: str) -> TaskRecord:
        repository_root = self._repository_root(path)
        task_file = self._tasks_root(repository_root) / task_id / "task.yaml"
        if not task_file.exists():
            raise ValueError(f"Task {task_id} was not found.")
        return self._load_task(task_file)

    def _repository_root(self, path: Path) -> Path:
        inspection = self._discovery.inspect(path)
        if inspection.repository_root is None:
            raise ValueError("Current path is not inside a Git repository.")
        return inspection.repository_root

    def _tasks_root(self, repository_root: Path) -> Path:
        tasks_root = repository_root / ".agentflow" / "tasks"
        if not tasks_root.exists():
            raise ValueError("AgentFlow is not initialized for this repository. Run `agentflow init --write` first.")
        return tasks_root

    def _load_task(self, task_file: Path) -> TaskRecord:
        loaded = yaml.safe_load(task_file.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"Task file {task_file} must contain a mapping.")
        return TaskRecord.model_validate(loaded)

    def _write(self, target_path: Path, content: str) -> str:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=target_path.parent, delete=False) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        temp_path.replace(target_path)
        return target_path.name

    def _json_dump(self, payload: object) -> str:
        import json

        return json.dumps(payload, indent=2) + "\n"
