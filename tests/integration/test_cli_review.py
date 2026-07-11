from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def _run_git(repository_root: Path, *args: str) -> None:
    completed = subprocess.run(["git", *args], cwd=repository_root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)


def _create_task(repository_root: Path) -> None:
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


def _write_state(repository_root: Path, state: str) -> None:
    task_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "task.yaml"
    state_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "state.json"
    task_file.write_text(task_file.read_text(encoding="utf-8").replace("current_state: created", f"current_state: {state}"), encoding="utf-8")
    state_file.write_text(
        state_file.read_text(encoding="utf-8").replace('"current_state": "created"', f'"current_state": "{state}"'),
        encoding="utf-8",
    )


def test_review_approved_transitions_to_final_review(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_task(repository_root)
    _write_state(repository_root, "code_review")
    (repository_root / ".agentflow" / "tasks" / "TASK-001" / "validation-results.json").write_text("[]\n", encoding="utf-8")

    result = runner.invoke(app, ["review", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 0
    assert '"verdict": "approved"' in result.stdout
    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"current_state": "final_review"' in status_result.stdout


def test_review_rejected_transitions_to_repairing(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_task(repository_root)
    _write_state(repository_root, "code_review")
    (repository_root / ".agentflow" / "tasks" / "TASK-001" / "validation-results.json").write_text(
        '[{"validator_id":"bad","status":"failed","summary":"failed","raw_log_path":null,"metrics":{}}]\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["review", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 6
    assert '"verdict": "rejected"' in result.stdout
    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"current_state": "repairing"' in status_result.stdout