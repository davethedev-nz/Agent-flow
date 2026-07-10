from pathlib import Path
import sys

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def _create_initialized_task(repository_root: Path) -> None:
    (repository_root / ".git").mkdir(parents=True)
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root), "--title", "Demo task"]).exit_code == 0


def test_agent_run_fake_adapter_persists_result(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_initialized_task(repository_root)

    result = runner.invoke(
        app,
        ["agent-run", "TASK-001", str(repository_root), "--role", "planner", "--prompt", "Plan this change", "--json"],
    )

    assert result.exit_code == 0
    assert '"provider": "fake"' in result.stdout
    assert '"summary": "Fake planner run completed."' in result.stdout
    runs_dir = repository_root / ".agentflow" / "tasks" / "TASK-001" / "runs"
    assert runs_dir.exists()
    assert any(runs_dir.iterdir())


def test_agent_run_subprocess_text_adapter_returns_stdout(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_initialized_task(repository_root)

    result = runner.invoke(
        app,
        [
            "agent-run",
            "TASK-001",
            str(repository_root),
            "--role",
            "implementer",
            "--adapter",
            "subprocess-text",
            "--command",
            sys.executable,
            "--command",
            "-c",
            "--command",
            "import sys; print(sys.argv[1])",
            "--prompt",
            "echo this prompt",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert '"provider": "subprocess-text"' in result.stdout
    assert '"stdout": "echo this prompt"' in result.stdout