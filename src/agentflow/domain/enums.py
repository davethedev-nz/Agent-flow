from __future__ import annotations

from enum import Enum


class TaskState(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    PLAN_REVIEW = "plan_review"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    REPAIRING = "repairing"
    CODE_REVIEW = "code_review"
    DOCUMENTING = "documenting"
    FINAL_REVIEW = "final_review"
    READY_TO_COMMIT = "ready_to_commit"
    COMPLETE = "complete"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class AgentRole(str, Enum):
    PLANNER = "planner"
    IMPLEMENTER = "implementer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    DOCUMENTER = "documenter"


class ReviewVerdict(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class FindingSeverity(str, Enum):
    BLOCKING = "blocking"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED_RISK = "accepted_risk"
    SUPERSEDED = "superseded"
