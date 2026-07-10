from pathlib import Path

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def test_task_create_writes_repository_local_files(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    init_result = runner.invoke(app, ["init", str(repository_root), "--write"])
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["task", "create", "TASK-001", str(repository_root), "--title", "Demo task", "--json"])

    assert result.exit_code == 0
    assert '"task_id": "TASK-001"' in result.stdout
    assert (repository_root / ".agentflow" / "tasks" / "TASK-001" / "task.yaml").exists()
    assert (repository_root / ".agentflow" / "tasks" / "TASK-001" / "requirements.md").exists()
    assert (repository_root / ".agentflow" / "tasks" / "TASK-001" / "acceptance-criteria.md").exists()
    assert (repository_root / ".agentflow" / "tasks" / "TASK-001" / "plan.md").exists()
    assert (repository_root / ".agentflow" / "tasks" / "TASK-001" / "state.json").exists()
    assert (repository_root / ".agentflow" / "tasks" / "TASK-001" / "events.jsonl").exists()


def test_task_list_and_show_return_created_task(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root), "--title", "Demo task"]).exit_code == 0

    list_result = runner.invoke(app, ["task", "list", str(repository_root), "--json"])
    show_result = runner.invoke(app, ["task", "show", "TASK-001", str(repository_root), "--json"])

    assert list_result.exit_code == 0
    assert '"task_id": "TASK-001"' in list_result.stdout
    assert '"title": "Demo task"' in list_result.stdout
    assert show_result.exit_code == 0
    assert '"current_state": "created"' in show_result.stdout


def test_task_create_rejects_duplicate_task_id(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root)]).exit_code == 0

    result = runner.invoke(app, ["task", "create", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 1
    assert '"Task TASK-001 already exists."' in result.stdout


def test_task_commands_require_initialized_repository(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)

    result = runner.invoke(app, ["task", "create", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 1
    assert '"message": "AgentFlow is not initialized for this repository. Run `agentflow init --write` first."' in result.stdout