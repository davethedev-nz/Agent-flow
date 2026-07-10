from pathlib import Path

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def _create_initialized_task(repository_root: Path) -> None:
    import subprocess

    repository_root.mkdir(parents=True)
    for argv in (
        ["git", "init", "-b", "main"],
        ["git", "config", "user.email", "test@example.com"],
        ["git", "config", "user.name", "Test User"],
    ):
        completed = subprocess.run(argv, cwd=repository_root, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise AssertionError(completed.stderr or completed.stdout)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (repository_root / "README.md").write_text("demo\n", encoding="utf-8")
    for argv in (
        ["git", "add", "."],
        ["git", "commit", "-m", "init"],
    ):
        completed = subprocess.run(argv, cwd=repository_root, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise AssertionError(completed.stderr or completed.stdout)
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root), "--title", "Demo task"]).exit_code == 0


def test_plan_generates_plan_file_and_moves_to_plan_review(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_initialized_task(repository_root)

    result = runner.invoke(app, ["plan", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 0
    assert '"status": "plan_review"' in result.stdout
    plan_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "plan.md"
    assert plan_file.exists()
    assert "# Plan" in plan_file.read_text(encoding="utf-8")

    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"current_state": "plan_review"' in status_result.stdout


def test_approve_plan_records_approval_and_moves_to_implementing(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_initialized_task(repository_root)
    assert runner.invoke(app, ["plan", "TASK-001", str(repository_root)]).exit_code == 0

    result = runner.invoke(app, ["approve-plan", "TASK-001", str(repository_root), "--reason", "Looks good", "--json"])

    assert result.exit_code == 0
    assert '"current_state": "implementing"' in result.stdout
    approvals_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "approvals.json"
    assert approvals_file.exists()
    assert '"plan_approved": true' in approvals_file.read_text(encoding="utf-8")


def test_plan_rejects_invalid_starting_state(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_initialized_task(repository_root)
    assert runner.invoke(app, ["block", "TASK-001", str(repository_root)]).exit_code == 0

    result = runner.invoke(app, ["plan", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 1
    assert '"Plan generation is only allowed from created or planning, not blocked."' in result.stdout