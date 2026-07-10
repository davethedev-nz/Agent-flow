from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def _run_git(repository_root: Path, *args: str) -> None:
    completed = subprocess.run(["git", *args], cwd=repository_root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)


def _create_ready_task(repository_root: Path) -> None:
    repository_root.mkdir(parents=True)
    _run_git(repository_root, "init", "-b", "main")
    _run_git(repository_root, "config", "user.email", "test@example.com")
    _run_git(repository_root, "config", "user.name", "Test User")
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (repository_root / "README.md").write_text("demo\n", encoding="utf-8")
    _run_git(repository_root, "add", ".")
    _run_git(repository_root, "commit", "-m", "init")
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root)]).exit_code == 0


def test_command_run_executes_allowlisted_command(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_ready_task(repository_root)

    result = runner.invoke(app, ["command-run", "TASK-001", str(repository_root), "--command", "git", "--command", "status", "--command", "--short", "--json"])

    assert result.exit_code == 0
    assert '"exit_code": 0' in result.stdout
    assert '"approval_required": false' in result.stdout


def test_command_run_requests_approval_for_blocked_command(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_ready_task(repository_root)

    result = runner.invoke(app, ["command-run", "TASK-001", str(repository_root), "--command", "git", "--command", "push", "--json"])

    assert result.exit_code == 4
    assert '"approval_required": true' in result.stdout
    pending = repository_root / ".agentflow" / "tasks" / "TASK-001" / "command-approval.json"
    assert pending.exists()


def test_approve_and_reject_command_flow(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_ready_task(repository_root)
    assert runner.invoke(app, ["command-run", "TASK-001", str(repository_root), "--command", "git", "--command", "push", "--json"]).exit_code == 4

    reject_result = runner.invoke(app, ["reject-command", "TASK-001", str(repository_root), "--json"])
    assert reject_result.exit_code == 0
    assert '"status": "rejected"' in reject_result.stdout

    assert runner.invoke(app, ["command-run", "TASK-001", str(repository_root), "--command", "git", "--command", "status", "--command", "--short", "--json"]).exit_code == 0
    assert runner.invoke(app, ["command-run", "TASK-001", str(repository_root), "--command", "git", "--command", "push", "--json"]).exit_code == 4
    approve_result = runner.invoke(app, ["approve-command", "TASK-001", str(repository_root), "--json"])
    assert approve_result.exit_code == 0 or approve_result.exit_code == 1
    assert '"task_id": "TASK-001"' in approve_result.stdout