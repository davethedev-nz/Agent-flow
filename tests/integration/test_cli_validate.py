from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def _run_git(repository_root: Path, *args: str) -> None:
    completed = subprocess.run(["git", *args], cwd=repository_root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)


def _create_implementing_task(repository_root: Path) -> None:
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
    assert runner.invoke(app, ["plan", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["approve-plan", "TASK-001", str(repository_root)]).exit_code == 0


def test_validate_passes_and_transitions_to_code_review(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_implementing_task(repository_root)
    (repository_root / ".agentflow" / "validation.yaml").write_text(
        "schema_version: 1\nvalidators:\n  - validator_id: git_status\n    description: git status\n    command: [git, status, --short]\n    timeout_seconds: 30\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 0
    assert '"status": "passed"' in result.stdout
    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"current_state": "code_review"' in status_result.stdout


def test_validate_failure_transitions_to_repairing(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_implementing_task(repository_root)
    (repository_root / ".agentflow" / "validation.yaml").write_text(
        "schema_version: 1\nvalidators:\n  - validator_id: bad_cmd\n    description: bad\n    command: [git, definitely-not-a-command]\n    timeout_seconds: 30\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["validate", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 6
    assert '"status": "failed"' in result.stdout
    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"current_state": "repairing"' in status_result.stdout