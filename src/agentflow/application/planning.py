from __future__ import annotations

import json
from pathlib import Path

from agentflow.application.agent_execution import AgentExecutionService
from agentflow.application.state_transitions import TaskTransitionService
from agentflow.application.task_records import TaskRecordService
from agentflow.domain.enums import AgentRole, TaskState
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class PlanningService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._transitions = TaskTransitionService(discovery)
        self._agents = AgentExecutionService(discovery)

    def generate_plan(self, path: Path, task_id: str, adapter: str = "fake", command: list[str] | None = None) -> str:
        task_root = self._records.task_root(path, task_id)
        task = self._records.show(path, task_id)
        state = self._records.load_state(path, task_id)

        if state.current_state == TaskState.CREATED:
            self._transitions.transition(path, task_id, TaskState.PLANNING, reason="Plan requested", event_type="plan_requested")
        elif state.current_state != TaskState.PLANNING:
            raise ValueError(f"Plan generation is only allowed from created or planning, not {state.current_state.value}.")

        requirements = (task_root / "requirements.md").read_text(encoding="utf-8")
        acceptance = (task_root / "acceptance-criteria.md").read_text(encoding="utf-8")
        prompt = (
            f"Task: {task.title}\n\n"
            f"Requirements:\n{requirements}\n\n"
            f"Acceptance Criteria:\n{acceptance}\n\n"
            "Produce a concise implementation plan with steps, risks, validation commands, and path scope."
        )
        result = self._agents.run(path, task_id, AgentRole.PLANNER, prompt, adapter, command)

        plan_markdown = (
            "# Plan\n\n"
            f"## Summary\n\n{result.summary}\n\n"
            "## Proposed Steps\n\n"
            "1. Inspect the bounded task context.\n"
            "2. Implement the smallest change that satisfies the requirements.\n"
            "3. Validate the affected behavior with deterministic checks.\n\n"
            "## Validation\n\n"
            "- Run project validation commands relevant to the changed paths.\n\n"
            "## Risks\n\n"
            "- Unknown edge cases remain until deterministic validation and review run.\n\n"
            "## Path Scope\n\n"
            "- Restrict work to the files directly needed for this task.\n"
        )
        self._records.write_text(task_root / "plan.md", plan_markdown)
        self._transitions.transition(path, task_id, TaskState.PLAN_REVIEW, reason="Plan generated", event_type="plan_generated")
        return plan_markdown

    def record_plan_approval(self, path: Path, task_id: str, reason: str | None = None) -> None:
        task_root = self._records.task_root(path, task_id)
        approval_payload = {
            "plan_approved": True,
            "reason": reason,
        }
        self._records.write_text(task_root / "approvals.json", json.dumps(approval_payload, indent=2) + "\n")
