from pathlib import Path

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def test_project_inspect_json_reports_repository_root(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    nested_path = repository_root / "pkg" / "module"
    nested_path.mkdir(parents=True)
    (repository_root / ".git").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    result = runner.invoke(app, ["project", "inspect", str(nested_path), "--json"])

    assert result.exit_code == 0
    assert '"is_git_repository": true' in result.stdout
    assert f'"repository_root": "{repository_root}"' in result.stdout
    assert '"stack_hints": [' in result.stdout
    assert '"python"' in result.stdout


def test_project_inspect_json_reports_non_repository_path(tmp_path: Path) -> None:
    result = runner.invoke(app, ["project", "inspect", str(tmp_path), "--json"])

    assert result.exit_code == 0
    assert '"is_git_repository": false' in result.stdout
    assert '"repository_root": null' in result.stdout