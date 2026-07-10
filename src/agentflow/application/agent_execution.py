from __future__ import annotations

import json
import uuid
from pathlib import Path

from agentflow.adapters.fake import FakeAgentAdapter
from agentflow.adapters.subprocess_text import SubprocessTextAgentAdapter
from agentflow.application.task_records import TaskRecordService
from agentflow.domain.enums import AgentRole
from agentflow.domain.models import AgentRequest, AgentResult
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class AgentExecutionService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)

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
        request = AgentRequest(
            task_id=task_id,
            role=role,
            prompt=prompt,
            working_directory=task.repository_root,
            repository_root=task.repository_root,
            expected_output_schema="generic",
        )

        adapter = self._adapter(adapter_name, command)
        result = adapter.execute(request)
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        runs_root = task_root / "runs"
        runs_root.mkdir(parents=True, exist_ok=True)
        result_path = runs_root / f"{run_id}.json"
        result_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
        result.raw_output_location = result_path
        return result

    def _adapter(self, adapter_name: str, command: list[str] | None) -> FakeAgentAdapter | SubprocessTextAgentAdapter:
        if adapter_name == "fake":
            return FakeAgentAdapter()
        if adapter_name == "subprocess-text":
            return SubprocessTextAgentAdapter(command or [])
        raise ValueError(f"Unsupported adapter {adapter_name}.")
