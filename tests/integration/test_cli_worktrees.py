from pathlib import Path

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def _run_git(repository_root: Path, *args: str) -> None:
    import subprocess

    completed = subprocess.run(["git", *args], cwd=repository_root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)


def _create_committed_repo(repository_root: Path) -> None:
    repository_root.mkdir(parents=True)
    _run_git(repository_root, "init", "-b", "main")
    _run_git(repository_root, "config", "user.email", "test@example.com")
    _run_git(repository_root, "config", "user.name", "Test User")
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (repository_root / "README.md").write_text("demo\n", encoding="utf-8")
    _run_git(repository_root, "add", ".")
    _run_git(repository_root, "commit", "-m", "init")


def test_approve_plan_creates_task_branch_and_worktree(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_committed_repo(repository_root)
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["plan", "TASK-001", str(repository_root)]).exit_code == 0

    result = runner.invoke(app, ["approve-plan", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 0
    worktree_metadata = repository_root / ".agentflow" / "tasks" / "TASK-001" / "worktree.json"
    assert worktree_metadata.exists()

    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"worktree_path":' in status_result.stdout
    assert '"current_state": "implementing"' in status_result.stdout


def test_approve_plan_reuses_existing_worktree_metadata(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_committed_repo(repository_root)
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["plan", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["approve-plan", "TASK-001", str(repository_root)]).exit_code == 0

    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"worktree_path":' in status_result.stdout