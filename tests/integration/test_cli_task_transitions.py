from pathlib import Path

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def _create_initialized_task(repository_root: Path) -> None:
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root), "--title", "Demo task"]).exit_code == 0


def _write_state(repository_root: Path, state: str) -> None:
    task_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "task.yaml"
    state_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "state.json"
    task_text = task_file.read_text(encoding="utf-8").replace("current_state: created", f"current_state: {state}")
    task_file.write_text(task_text, encoding="utf-8")
    state_text = state_file.read_text(encoding="utf-8").replace('"current_state": "created"', f'"current_state": "{state}"')
    state_file.write_text(state_text, encoding="utf-8")


def test_task_status_reports_allowed_transitions(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_initialized_task(repository_root)

    result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 0
    assert '"current_state": "created"' in result.stdout
    assert '"previous_state": null' in result.stdout
    assert '"planning"' in result.stdout
    assert '"blocked"' in result.stdout


def test_approve_plan_transitions_from_plan_review_to_implementing(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_initialized_task(repository_root)
    _write_state(repository_root, "plan_review")

    result = runner.invoke(app, ["approve-plan", "TASK-001", str(repository_root), "--reason", "Plan approved", "--json"])

    assert result.exit_code == 0
    assert '"previous_state": "plan_review"' in result.stdout
    assert '"current_state": "implementing"' in result.stdout
    assert '"transition_reason": "Plan approved"' in result.stdout

    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"previous_state": "plan_review"' in status_result.stdout
    assert '"transition_reason": "Plan approved"' in status_result.stdout


def test_invalid_transition_is_rejected(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_initialized_task(repository_root)

    result = runner.invoke(app, ["approve-plan", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 1
    assert '"Transition from created to implementing is not allowed."' in result.stdout


def test_block_and_resume_allow_guarded_recovery(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_initialized_task(repository_root)

    block_result = runner.invoke(app, ["block", "TASK-001", str(repository_root), "--reason", "Waiting for clarification", "--json"])
    resume_result = runner.invoke(app, ["resume", "TASK-001", str(repository_root), "--to", "planning", "--reason", "Requirements clarified", "--json"])

    assert block_result.exit_code == 0
    assert '"current_state": "blocked"' in block_result.stdout
    assert '"transition_reason": "Waiting for clarification"' in block_result.stdout
    assert resume_result.exit_code == 0
    assert '"current_state": "planning"' in resume_result.stdout
    assert '"transition_reason": "Requirements clarified"' in resume_result.stdout