from __future__ import annotations

import json
from pathlib import Path

from agentflow.application.agent_execution import AgentExecutionService
from agentflow.application.path_policy import PathPolicyViolationError
from agentflow.application.state_transitions import TaskTransitionService
from agentflow.application.task_events import TaskEventService
from agentflow.application.task_records import TaskRecordService
from agentflow.domain.enums import AgentRole, TaskState
from agentflow.domain.models import AgentResult
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class DocumentationService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._events = TaskEventService(discovery)
        self._transitions = TaskTransitionService(discovery)
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
        if state.current_state != TaskState.FINAL_REVIEW:
            raise ValueError(
                f"Documentation pass is only allowed from final_review, not {state.current_state.value}."
            )

        self._transitions.transition(
            path,
            task_id,
            TaskState.DOCUMENTING,
            reason="Documentation pass started",
            event_type="documentation_started",
        )

        documenter_prompt = (
            prompt
            or "Update documentation to reflect the verified behavior. "
            "Only edit documentation paths allowed by policy."
        )

        try:
            result = self._agents.run(path, task_id, AgentRole.DOCUMENTER, documenter_prompt, adapter, command)
        except PathPolicyViolationError:
            raise

        task_root = self._records.task_root(path, task_id)
        self._records.write_text(
            task_root / "documentation-result.json",
            json.dumps(result.model_dump(mode="json"), indent=2) + "\n",
        )
        self._events.append(
            path,
            task_id,
            "documentation_completed",
            None,
            None,
            payload={
                "changed_files": [str(changed_path) for changed_path in result.changed_files],
                "provider": result.provider,
            },
        )
        self._transitions.transition(
            path,
            task_id,
            TaskState.FINAL_REVIEW,
            reason="Documentation pass completed",
            event_type="documentation_finalized",
        )
        return result