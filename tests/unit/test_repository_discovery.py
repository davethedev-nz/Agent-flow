from pathlib import Path

from agentflow.infrastructure.repository_discovery import FilesystemRepositoryDiscovery


def test_finds_repository_root_from_nested_directory(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    nested_path = repository_root / "src" / "feature"
    nested_path.mkdir(parents=True)
    (repository_root / ".git").mkdir()

    discovery = FilesystemRepositoryDiscovery()

    assert discovery.find_repository_root(nested_path) == repository_root


def test_returns_none_for_non_repository_path(tmp_path: Path) -> None:
    discovery = FilesystemRepositoryDiscovery()

    assert discovery.find_repository_root(tmp_path) is None


def test_detects_supported_stack_hints(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / ".git").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (repository_root / "package.json").write_text("{}\n", encoding="utf-8")
    (repository_root / "service.csproj").write_text("<Project />\n", encoding="utf-8")
    (repository_root / "main.tf").write_text("terraform {}\n", encoding="utf-8")

    discovery = FilesystemRepositoryDiscovery()

    assert discovery.detect_stack_hints(repository_root) == [
        "python",
        "node-typescript",
        "dotnet",
        "terraform",
    ]


def test_inspect_marks_agentflow_initialization(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / ".git").mkdir()
    (repository_root / ".agentflow").mkdir()

    inspection = FilesystemRepositoryDiscovery().inspect(repository_root)

    assert inspection.is_git_repository is True
    assert inspection.agentflow_initialized is True
    assert inspection.repository_root == repository_root