from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def _run_git(repository_root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=repository_root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return completed.stdout.strip()


def _create_task_with_worktree(repository_root: Path) -> Path:
    repository_root.mkdir(parents=True)
    _run_git(repository_root, "init", "-b", "main")
    _run_git(repository_root, "config", "user.email", "test@example.com")
    _run_git(repository_root, "config", "user.name", "Test User")
    (repository_root / "src").mkdir()
    (repository_root / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (repository_root / "README.md").write_text("demo\n", encoding="utf-8")
    _run_git(repository_root, "add", ".")
    _run_git(repository_root, "commit", "-m", "init")

    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["plan", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["approve-plan", "TASK-001", str(repository_root)]).exit_code == 0

    worktree_path = repository_root.parent / ".worktrees" / repository_root.name / "TASK-001"
    return worktree_path


def _write_state(repository_root: Path, state: str) -> None:
    task_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "task.yaml"
    state_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "state.json"
    task_file.write_text(task_file.read_text(encoding="utf-8").replace("current_state: implementing", f"current_state: {state}"), encoding="utf-8")
    state_file.write_text(
        state_file.read_text(encoding="utf-8").replace('"current_state": "implementing"', f'"current_state": "{state}"'),
        encoding="utf-8",
    )


def test_approve_commit_creates_local_commit_and_completes_task(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    worktree_path = _create_task_with_worktree(repository_root)
    _write_state(repository_root, "final_review")
    (worktree_path / "src" / "main.py").write_text("print('updated')\n", encoding="utf-8")

    result = runner.invoke(app, ["approve-commit", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 0
    assert '"task_id": "TASK-001"' in result.stdout
    assert '"commit":' in result.stdout

    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"current_state": "complete"' in status_result.stdout
    completion_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "completion.json"
    assert completion_file.exists()