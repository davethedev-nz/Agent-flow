from __future__ import annotations

from pathlib import Path

from agentflow.domain.project import ProjectInspection


class FilesystemRepositoryDiscovery:
    """Filesystem-based repository discovery for slice 1."""

    def inspect(self, start_path: Path) -> ProjectInspection:
        requested_path = start_path.resolve()
        search_path = requested_path if requested_path.is_dir() else requested_path.parent
        repository_root = self.find_repository_root(search_path)
        stack_hints = self.detect_stack_hints(repository_root) if repository_root else []

        return ProjectInspection(
            requested_path=requested_path,
            repository_root=repository_root,
            is_git_repository=repository_root is not None,
            agentflow_initialized=bool(repository_root and (repository_root / ".agentflow").exists()),
            stack_hints=stack_hints,
        )

    def find_repository_root(self, start_path: Path) -> Path | None:
        current = start_path.resolve()

        for candidate in (current, *current.parents):
            if (candidate / ".git").exists():
                return candidate

        return None

    def detect_stack_hints(self, repository_root: Path) -> list[str]:
        hints: list[str] = []

        if self._has_any(repository_root, "pyproject.toml", "requirements.txt"):
            hints.append("python")

        if self._has_any(repository_root, "package.json", "tsconfig.json"):
            hints.append("node-typescript")

        if any(repository_root.glob("*.sln")) or any(repository_root.rglob("*.csproj")):
            hints.append("dotnet")

        if any(repository_root.rglob("*.tf")):
            hints.append("terraform")

        return hints

    def _has_any(self, repository_root: Path, *names: str) -> bool:
        return any((repository_root / name).exists() for name in names)