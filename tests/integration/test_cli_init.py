from pathlib import Path

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def test_init_preview_json_for_python_repository(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "tests").mkdir()
    (repository_root / "docs").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    result = runner.invoke(app, ["init", str(repository_root), "--json"])

    assert result.exit_code == 0
    assert f'"repository_root": "{repository_root}"' in result.stdout
    assert '"selected_profile": "python"' in result.stdout
    assert '".agentflow/config.yaml"' in result.stdout
    assert '"status": "create"' in result.stdout
    assert '".vscode/tasks.json"' not in result.stdout


def test_init_preview_json_can_include_vscode_tasks(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    result = runner.invoke(app, ["init", str(repository_root), "--vscode-tasks", "--json"])

    assert result.exit_code == 0
    assert '".vscode/tasks.json"' in result.stdout
    assert '"status": "create"' in result.stdout


def test_init_write_creates_files_and_is_idempotent(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    first_result = runner.invoke(app, ["init", str(repository_root), "--write", "--json"])

    assert first_result.exit_code == 0
    assert (repository_root / ".agentflow" / "config.yaml").exists()
    assert '"written_files": [' in first_result.stdout

    second_result = runner.invoke(app, ["init", str(repository_root), "--write", "--json"])

    assert second_result.exit_code == 0
    assert '"conflict_files": []' in second_result.stdout
    assert '"unchanged_files": [' in second_result.stdout


def test_init_write_with_vscode_tasks_creates_expected_file(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    result = runner.invoke(app, ["init", str(repository_root), "--write", "--vscode-tasks", "--json"])

    assert result.exit_code == 0
    tasks_path = repository_root / ".vscode" / "tasks.json"
    assert tasks_path.exists()
    assert '"written_files": [' in result.stdout
    assert '".vscode/tasks.json"' in result.stdout

    tasks_content = tasks_path.read_text(encoding="utf-8")
    assert '"command": "agentflow doctor"' in tasks_content
    assert '"command": "agentflow project-inspect"' in tasks_content


def test_init_write_with_vscode_tasks_detects_conflicts(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    first_result = runner.invoke(app, ["init", str(repository_root), "--write", "--vscode-tasks", "--json"])
    assert first_result.exit_code == 0

    tasks_path = repository_root / ".vscode" / "tasks.json"
    tasks_path.write_text('{"version":"9.9.9"}\n', encoding="utf-8")

    second_result = runner.invoke(app, ["init", str(repository_root), "--write", "--vscode-tasks", "--json"])

    assert second_result.exit_code == 1
    assert '"conflict_files": [' in second_result.stdout
    assert '".vscode/tasks.json"' in second_result.stdout


def test_init_refuses_to_overwrite_existing_different_file(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    first_result = runner.invoke(app, ["init", str(repository_root), "--write", "--json"])
    assert first_result.exit_code == 0

    config_path = repository_root / ".agentflow" / "config.yaml"
    config_path.write_text("schema_version: 999\n", encoding="utf-8")

    second_result = runner.invoke(app, ["init", str(repository_root), "--write", "--json"])

    assert second_result.exit_code == 1
    assert '"conflict_files": [' in second_result.stdout
    assert '".agentflow/config.yaml"' in second_result.stdout


def test_init_fails_for_non_repository_path(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path), "--json"])

    assert result.exit_code == 1
    assert '"status": "error"' not in result.stdout
    assert '"is_git_repository": false' in result.stdout