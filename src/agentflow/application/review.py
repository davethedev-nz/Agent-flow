from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agentflow.application.agent_execution import AgentExecutionService
from agentflow.application.state_transitions import TaskTransitionService
from agentflow.application.task_events import TaskEventService
from agentflow.application.task_records import TaskRecordService
from agentflow.domain.enums import AgentRole, FindingSeverity, ReviewVerdict, TaskState
from agentflow.domain.models import Finding, ReviewResult, ValidationResult
from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


class ReviewService:
    def __init__(self, discovery: FilesystemRepositoryDiscovery) -> None:
        self._records = TaskRecordService(discovery)
        self._events = TaskEventService(discovery)
        self._transitions = TaskTransitionService(discovery)
        self._agents = AgentExecutionService(discovery)

    def review_task(self, path: Path, task_id: str, adapter: str = "fake", command: list[str] | None = None) -> ReviewResult:
        state = self._records.load_state(path, task_id)
        if state.current_state != TaskState.CODE_REVIEW:
            raise ValueError(f"Review is only allowed from code_review, not {state.current_state.value}.")

        task_root = self._records.task_root(path, task_id)
        validation_results = self._load_validation_results(task_root)
        findings = self._findings_from_validation(validation_results)

        prompt = (
            "Review the latest validation evidence and identify any blocking issues. "
            "Return concise, structured findings with required action."
        )
        agent_result = self._agents.run(path, task_id, AgentRole.REVIEWER, prompt, adapter, command)
        findings.extend(agent_result.findings)

        verdict = self._verdict(findings)
        review_result = ReviewResult(verdict=verdict, findings=findings, summary=f"Review completed with verdict {verdict.value}.")
        self._records.write_text(task_root / "findings.json", json.dumps([item.model_dump(mode="json") for item in findings], indent=2) + "\n")
        self._records.write_text(task_root / "review-result.json", json.dumps(review_result.model_dump(mode="json"), indent=2) + "\n")
        self._events.append(
            path,
            task_id,
            "review_completed",
            None,
            None,
            payload={"verdict": verdict.value, "findings": len(findings)},
        )

        if verdict == ReviewVerdict.APPROVED:
            self._transitions.transition(
                path,
                task_id,
                TaskState.FINAL_REVIEW,
                reason="Review approved",
                event_type="review_approved",
            )
        else:
            self._transitions.transition(
                path,
                task_id,
                TaskState.REPAIRING,
                reason="Review requires repair",
                event_type="review_rejected",
            )
        return review_result

    def _load_validation_results(self, task_root: Path) -> list[ValidationResult]:
        results_path = task_root / "validation-results.json"
        if not results_path.exists():
            return []
        loaded = json.loads(results_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            return []
        return [ValidationResult.model_validate(item) for item in loaded if isinstance(item, dict)]

    def _findings_from_validation(self, results: list[ValidationResult]) -> list[Finding]:
        findings: list[Finding] = []
        for result in results:
            if result.status == "passed":
                continue
            fingerprint = hashlib.sha256(f"validation:{result.validator_id}:{result.status}".encode("utf-8")).hexdigest()[:10]
            findings.append(
                Finding(
                    finding_id=f"FIND-{fingerprint}",
                    severity=FindingSeverity.BLOCKING,
                    category="validation",
                    title=f"Validator {result.validator_id} failed",
                    description=result.summary,
                    evidence=str(result.raw_log_path) if result.raw_log_path else "",
                    required_action="Fix validation failures and rerun validation.",
                )
            )
        return findings

    def _verdict(self, findings: list[Finding]) -> ReviewVerdict:
        has_blocking = any(item.severity in {FindingSeverity.BLOCKING, FindingSeverity.HIGH} for item in findings)
        return ReviewVerdict.REJECTED if has_blocking else ReviewVerdict.APPROVED