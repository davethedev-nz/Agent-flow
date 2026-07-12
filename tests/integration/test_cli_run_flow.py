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


def test_run_reaches_final_review_when_validation_passes(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_implementing_task(repository_root)
    (repository_root / ".agentflow" / "validation.yaml").write_text(
        "schema_version: 1\nvalidators:\n  - validator_id: git_status\n    description: git status\n    command: [git, status, --short]\n    timeout_seconds: 30\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["run", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 0
    assert '"final_state": "final_review"' in result.stdout


def test_run_blocks_when_repair_iterations_are_exhausted(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_implementing_task(repository_root)
    (repository_root / ".agentflow" / "validation.yaml").write_text(
        "schema_version: 1\nvalidators:\n  - validator_id: bad\n    description: bad\n    command: [git, definitely-not-a-command]\n    timeout_seconds: 30\n",
        encoding="utf-8",
    )
    task_file = repository_root / ".agentflow" / "tasks" / "TASK-001" / "task.yaml"
    task_file.write_text(
        task_file.read_text(encoding="utf-8") + "overrides:\n  autonomy:\n    maximum_repair_iterations: 1\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["run", "TASK-001", str(repository_root), "--json"])

    assert result.exit_code == 7
    assert '"final_state": "blocked"' in result.stdout


def test_run_can_include_optional_tester_and_documentation_passes(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_implementing_task(repository_root)
    (repository_root / "docs").mkdir()
    (repository_root / ".agentflow" / "validation.yaml").write_text(
        "schema_version: 1\nvalidators:\n  - validator_id: git_status\n    description: git status\n    command: [git, status, --short]\n    timeout_seconds: 30\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["run", "TASK-001", str(repository_root), "--with-tester", "--with-docs", "--json"],
    )

    assert result.exit_code == 0
    assert '"final_state": "final_review"' in result.stdout
    assert '"tester_pass": true' in result.stdout
    assert '"documentation_pass": true' in result.stdout
    assert (repository_root / ".agentflow" / "tasks" / "TASK-001" / "tester-result.json").exists()
    assert (repository_root / ".agentflow" / "tasks" / "TASK-001" / "documentation-result.json").exists()