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