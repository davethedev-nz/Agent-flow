from pathlib import Path

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def test_config_show_resolved_reports_project_origin(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / ".agentflow").mkdir()
    (repository_root / ".agentflow" / "config.yaml").write_text(
        "schema_version: 1\nproject:\n  id: demo\npaths:\n  source: [src]\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["config", "show", str(repository_root), "--resolved", "--json"])

    assert result.exit_code == 0
    assert '"project.id": {' in result.stdout
    assert '"value": "demo"' in result.stdout
    assert '"origin": "project:.agentflow/config.yaml"' in result.stdout
    assert '"efficiency.max_context_files": {' in result.stdout


def test_config_show_resolved_applies_user_override(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    user_config_root = tmp_path / "xdg"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / ".agentflow").mkdir()
    (user_config_root / "agentflow").mkdir(parents=True)
    (repository_root / ".agentflow" / "config.yaml").write_text(
        "schema_version: 1\nautonomy:\n  maximum_repair_iterations: 6\n",
        encoding="utf-8",
    )
    (user_config_root / "agentflow" / "config.yaml").write_text(
        "autonomy:\n  maximum_repair_iterations: 5\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["config", "show", str(repository_root), "--resolved", "--json"],
        env={"XDG_CONFIG_HOME": str(user_config_root)},
    )

    assert result.exit_code == 0
    assert '"autonomy.maximum_repair_iterations": {' in result.stdout
    assert '"value": 6' in result.stdout
    assert '"origin": "project:.agentflow/config.yaml"' in result.stdout


def test_config_show_reports_non_repository_path(tmp_path: Path) -> None:
    result = runner.invoke(app, ["config", "show", str(tmp_path), "--resolved", "--json"])

    assert result.exit_code == 1
    assert '"status": "error"' in result.stdout
    assert '"Current path is not inside a Git repository."' in result.stdout


def test_config_show_plain_output_is_human_readable(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / ".agentflow").mkdir()
    (repository_root / ".agentflow" / "config.yaml").write_text(
        "schema_version: 1\nproject:\n  id: demo\nautonomy:\n  maximum_repair_iterations: 6\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["config", "show", str(repository_root)])

    assert result.exit_code == 0
    assert "AgentFlow project configuration" in result.stdout
    assert "project.id" in result.stdout
    assert "demo" in result.stdout
    assert "autonomy.maximum_repair_iterations" in result.stdout


def test_config_show_resolved_applies_task_override(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    task_dir = repository_root / ".agentflow" / "tasks" / "TASK-001"
    (repository_root / ".git").mkdir(parents=True)
    task_dir.mkdir(parents=True)
    (repository_root / ".agentflow" / "config.yaml").write_text(
        "schema_version: 1\nautonomy:\n  maximum_repair_iterations: 6\n",
        encoding="utf-8",
    )
    (task_dir / "task.yaml").write_text(
        "task_id: TASK-001\noverrides:\n  autonomy:\n    maximum_repair_iterations: 2\n  efficiency:\n    max_context_files: 6\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["config", "show", str(repository_root), "--resolved", "--task-id", "TASK-001", "--json"],
    )

    assert result.exit_code == 0
    assert '"autonomy.maximum_repair_iterations": {' in result.stdout
    assert '"value": 2' in result.stdout
    assert '"origin": "task:.agentflow/tasks/TASK-001/task.yaml"' in result.stdout
    assert '"efficiency.max_context_files": {' in result.stdout
    assert '"value": 6' in result.stdout