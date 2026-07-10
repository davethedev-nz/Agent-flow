from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from agentflow.domain.models import AgentRequest, AgentResult, TaskDefinition, ValidationResult


class AgentAdapter(Protocol):
    def execute(self, request: AgentRequest) -> AgentResult:
        """Run a bounded agent task and return a validated result."""


class GitService(Protocol):
    def discover_repository_root(self, start_path: Path) -> Path:
        """Return the enclosing repository root for a target path."""


class WorktreeService(Protocol):
    def ensure_task_worktree(self, task_id: str, repository_root: Path) -> Path:
        """Create or return the implementation worktree for a task."""


class CommandRunner(Protocol):
    def run(self, argv: Sequence[str], working_directory: Path, timeout_seconds: int) -> ValidationResult:
        """Execute a command without invoking a shell."""


class PathPolicy(Protocol):
    def validate_changes(self, changed_paths: Sequence[Path]) -> list[str]:
        """Return policy violations for a set of changed paths."""


class ValidationService(Protocol):
    def run_for_task(self, task: TaskDefinition) -> list[ValidationResult]:
        """Run the configured validation pipeline for a task."""


class TaskRepository(Protocol):
    def create(self, task: TaskDefinition) -> None:
        """Persist a newly created task."""

    def get(self, task_id: str) -> TaskDefinition:
        """Load a task definition."""


class EventRepository(Protocol):
    def append(self, event_type: str, payload: dict[str, object]) -> None:
        """Append an immutable event."""


class ApprovalService(Protocol):
    def require(self, task_id: str, approval_type: str, payload: dict[str, object]) -> None:
        """Register a pending approval request."""


class ContextBuilder(Protocol):
    def build_for_role(self, task: TaskDefinition, role: str) -> list[Path]:
        """Construct a deterministic context pack for a task role."""


class ConfigurationResolver(Protocol):
    def resolve(self, repository_root: Path) -> dict[str, object]:
        """Resolve the effective configuration and annotate its origins."""


class Clock(Protocol):
    def now_iso(self) -> str:
        """Return the current time in ISO 8601 format."""
