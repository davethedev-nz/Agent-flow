from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path, PurePosixPath

import yaml

from agentflow.application.protocols import PathPolicy
from agentflow.domain.enums import AgentRole


class PathPolicyViolationError(ValueError):
    def __init__(self, violations: Sequence[str]) -> None:
        self.violations = list(violations)
        message = "Path policy violation detected: " + "; ".join(self.violations)
        super().__init__(message)


class RepositoryPathPolicy(PathPolicy):
    def __init__(self, repository_root: Path, role: AgentRole) -> None:
        self._repository_root = repository_root
        self._role = role
        self._policy_path = repository_root / ".agentflow" / "policies" / "paths.yaml"

        loaded = yaml.safe_load(self._policy_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"Path policy {self._policy_path} must contain a mapping.")

        editable = loaded.get("editable", {})
        if not isinstance(editable, dict):
            raise ValueError(f"Path policy {self._policy_path} must contain editable mappings.")

        self._editable_paths = {
            key: self._normalize_patterns(value)
            for key, value in editable.items()
            if isinstance(value, list)
        }
        self._read_only_paths = self._normalize_patterns(loaded.get("read_only", []))
        self._forbidden_paths = self._normalize_patterns(loaded.get("forbidden", []))

    @property
    def editable_paths(self) -> list[Path]:
        return [Path(pattern) for pattern in self._editable_paths.get(self._role.value, [])]

    @property
    def forbidden_paths(self) -> list[Path]:
        return [Path(pattern) for pattern in self._forbidden_paths]

    def validate_changes(self, changed_paths: Sequence[Path]) -> list[str]:
        violations: list[str] = []
        editable_patterns = self._editable_paths.get(self._role.value, [])

        for changed_path in changed_paths:
            relative_path = self._relative_path(changed_path)
            if relative_path is None:
                violations.append(f"{changed_path.as_posix()} is outside the repository root.")
                continue

            if self._matches_any(relative_path, self._forbidden_paths):
                violations.append(f"{relative_path} is forbidden for {self._role.value}.")
                continue

            if self._matches_any(relative_path, self._read_only_paths):
                violations.append(f"{relative_path} is read-only for {self._role.value}.")
                continue

            if not editable_patterns:
                violations.append(
                    f"No editable scope is configured for {self._role.value}; {relative_path} cannot be modified."
                )
                continue

            if not self._matches_any(relative_path, editable_patterns):
                violations.append(f"{relative_path} is outside the editable scope for {self._role.value}.")

        return violations

    def _relative_path(self, changed_path: Path) -> str | None:
        if changed_path.is_absolute():
            resolved = changed_path.resolve(strict=False)
            try:
                return resolved.relative_to(self._repository_root).as_posix()
            except ValueError:
                return None

        return self._strip_current_dir_prefix(changed_path.as_posix())

    def _matches_any(self, relative_path: str, patterns: Sequence[str]) -> bool:
        return any(self._matches_pattern(relative_path, pattern) for pattern in patterns)

    def _matches_pattern(self, relative_path: str, pattern: str) -> bool:
        normalized_pattern = self._strip_current_dir_prefix(pattern.replace("\\", "/")).rstrip("/")
        normalized_path = self._strip_current_dir_prefix(relative_path.replace("\\", "/"))

        if not normalized_pattern:
            return False

        if any(character in normalized_pattern for character in "*?[]"):
            return PurePosixPath(normalized_path).match(normalized_pattern)

        return normalized_path == normalized_pattern or normalized_path.startswith(f"{normalized_pattern}/")

    def _normalize_patterns(self, values: object) -> list[str]:
        if not isinstance(values, list):
            return []

        patterns: list[str] = []
        for value in values:
            if isinstance(value, str) and value.strip():
                patterns.append(value)
        return patterns

    def _strip_current_dir_prefix(self, path_value: str) -> str:
        normalized = path_value
        while normalized.startswith("./"):
            normalized = normalized[2:]
        return normalized