from __future__ import annotations

from pathlib import Path

from agentflow.application.agent_execution import AgentExecutionService
from agentflow.application.configuration_resolution import ConfigurationResolutionService
from agentflow.application.review import ReviewService
from agentflow.application.state_transitions import TaskTransitionService
from agentflow.application.task_records import TaskRecordService
from agentflow.application.validation import ValidationService
from agentflow.domain.enums import AgentRole, TaskState
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class RunFlowService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._transitions = TaskTransitionService(discovery)
        self._agent = AgentExecutionService(discovery)
        self._validation = ValidationService(discovery)
        self._review = ReviewService(discovery)
        self._config = ConfigurationResolutionService(discovery)

    def run_task(self, path: Path, task_id: str, adapter: str = "fake", command: list[str] | None = None) -> dict[str, object]:
        iteration = 0
        max_iterations = int(self._config.resolve(path, task_id=task_id).settings["autonomy.maximum_repair_iterations"].value)
        while iteration <= max_iterations:
            state = self._records.load_state(path, task_id).current_state
            if state == TaskState.IMPLEMENTING:
                self._agent.run(
                    path,
                    task_id,
                    AgentRole.IMPLEMENTER,
                    prompt="Implement the approved plan within policy scope.",
                    adapter_name=adapter,
                    command=command,
                )
                state = self._records.load_state(path, task_id).current_state

            if state == TaskState.REPAIRING:
                self._agent.run(
                    path,
                    task_id,
                    AgentRole.IMPLEMENTER,
                    prompt="Repair unresolved issues from validation and review.",
                    adapter_name=adapter,
                    command=command,
                )
                self._transitions.transition(
                    path,
                    task_id,
                    TaskState.VALIDATING,
                    reason="Repair iteration completed",
                    event_type="repair_iteration_completed",
                )

            state = self._records.load_state(path, task_id).current_state
            if state == TaskState.VALIDATING:
                self._validation.run_for_task(path, task_id)
                state = self._records.load_state(path, task_id).current_state

            if state == TaskState.CODE_REVIEW:
                self._review.review_task(path, task_id, adapter=adapter, command=command)
                state = self._records.load_state(path, task_id).current_state

            if state == TaskState.FINAL_REVIEW:
                return {
                    "task_id": task_id,
                    "final_state": state.value,
                    "repair_iterations": iteration,
                    "status": "ready_for_final_approval",
                }

            if state == TaskState.REPAIRING:
                iteration += 1
                if iteration > max_iterations:
                    self._transitions.transition(
                        path,
                        task_id,
                        TaskState.BLOCKED,
                        reason="Maximum repair iterations reached",
                        event_type="task_blocked",
                    )
                    return {
                        "task_id": task_id,
                        "final_state": TaskState.BLOCKED.value,
                        "repair_iterations": iteration,
                        "status": "blocked",
                    }
                continue

            if state in {TaskState.BLOCKED, TaskState.CANCELLED, TaskState.COMPLETE}:
                return {
                    "task_id": task_id,
                    "final_state": state.value,
                    "repair_iterations": iteration,
                    "status": "stopped",
                }

            raise ValueError(f"Run flow cannot continue from state {state.value}.")

        raise ValueError("Run flow exceeded configured repair iterations.")