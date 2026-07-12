from __future__ import annotations

import json
from pathlib import Path

from agentflow.application.agent_execution import AgentExecutionService
from agentflow.application.task_events import TaskEventService
from agentflow.application.task_records import TaskRecordService
from agentflow.domain.enums import AgentRole, TaskState
from agentflow.domain.models import AgentResult
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class TesterService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._events = TaskEventService(discovery)
        self._agents = AgentExecutionService(discovery)

    def run_for_task(
        self,
        path: Path,
        task_id: str,
        adapter: str = "fake",
        command: list[str] | None = None,
        prompt: str | None = None,
    ) -> AgentResult:
        state = self._records.load_state(path, task_id)
        if state.current_state not in {TaskState.CODE_REVIEW, TaskState.FINAL_REVIEW, TaskState.REPAIRING}:
            raise ValueError(
                "Tester pass is only allowed from code_review, final_review, or repairing, "
                f"not {state.current_state.value}."
            )

        tester_prompt = (
            prompt
            or "Improve or add tests for covered behavior while staying strictly within test paths."
        )
        result = self._agents.run(path, task_id, AgentRole.TESTER, tester_prompt, adapter, command)

        task_root = self._records.task_root(path, task_id)
        self._records.write_text(
            task_root / "tester-result.json",
            json.dumps(result.model_dump(mode="json"), indent=2) + "\n",
        )
        self._events.append(
            path,
            task_id,
            "tester_completed",
            None,
            None,
            payload={
                "changed_files": [str(changed_path) for changed_path in result.changed_files],
                "provider": result.provider,
            },
        )
        return result