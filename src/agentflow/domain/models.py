from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from agentflow.domain.enums import AgentRole, FindingSeverity, FindingStatus, ReviewVerdict, TaskState


class TaskReference(BaseModel):
    task_id: str
    repository_root: Path
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AcceptanceCriterion(BaseModel):
    criterion_id: str
    text: str


class TaskDefinition(BaseModel):
    reference: TaskReference
    title: str
    requirements: list[str] = Field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = Field(default_factory=list)
    current_state: TaskState = TaskState.CREATED


class AgentRequest(BaseModel):
    task_id: str
    role: AgentRole
    prompt: str
    working_directory: Path
    repository_root: Path
    allowed_paths: list[Path] = Field(default_factory=list)
    forbidden_paths: list[Path] = Field(default_factory=list)
    allowed_commands: list[str] = Field(default_factory=list)
    forbidden_command_patterns: list[str] = Field(default_factory=list)
    context_files: list[Path] = Field(default_factory=list)
    iteration_number: int = 0
    timeout_seconds: int = 900
    maximum_output_bytes: int = 200_000
    expected_output_schema: str
    task_specific_instructions: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    finding_id: str
    severity: FindingSeverity
    category: str
    title: str
    file: str | None = None
    line: int | None = None
    description: str
    evidence: str
    required_action: str
    status: FindingStatus = FindingStatus.OPEN
    first_seen_iteration: int = 1
    last_seen_iteration: int = 1
    resolution_evidence: str | None = None
    related_acceptance_criterion: str | None = None


class AgentExecutionMetadata(BaseModel):
    provider: str
    model: str | None = None
    exit_code: int | None = None
    started_at: datetime
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    timeout: bool = False
    usage_metadata: dict[str, object] = Field(default_factory=dict)
    cost_metadata: dict[str, object] = Field(default_factory=dict)


class AgentResult(BaseModel):
    success: bool
    provider: str
    role: AgentRole
    summary: str
    changed_files: list[Path] = Field(default_factory=list)
    commands_requested: list[str] = Field(default_factory=list)
    commands_run: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    structured_output: dict[str, object] = Field(default_factory=dict)
    raw_output_location: Path | None = None
    metadata: AgentExecutionMetadata


class ValidationResult(BaseModel):
    validator_id: str
    status: str
    summary: str
    raw_log_path: Path | None = None
    metrics: dict[str, object] = Field(default_factory=dict)


class ReviewResult(BaseModel):
    verdict: ReviewVerdict
    findings: list[Finding] = Field(default_factory=list)
    summary: str
