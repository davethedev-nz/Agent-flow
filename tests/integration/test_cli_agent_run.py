from pathlib import Path
import subprocess
import sys

from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def _run_git(repository_root: Path, *args: str) -> None:
    completed = subprocess.run(["git", *args], cwd=repository_root, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)


def _create_committed_repo(repository_root: Path) -> None:
    repository_root.mkdir(parents=True)
    _run_git(repository_root, "init", "-b", "main")
    _run_git(repository_root, "config", "user.email", "test@example.com")
    _run_git(repository_root, "config", "user.name", "Test User")
    (repository_root / "src").mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (repository_root / "README.md").write_text("demo\n", encoding="utf-8")
    _run_git(repository_root, "add", ".")
    _run_git(repository_root, "commit", "-m", "init")


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


def test_agent_run_blocks_out_of_scope_changes(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_committed_repo(repository_root)
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["plan", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["approve-plan", "TASK-001", str(repository_root)]).exit_code == 0

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
            (
                "from pathlib import Path; "
                "Path('docs/runbook.md').parent.mkdir(parents=True, exist_ok=True); "
                "Path('docs/runbook.md').write_text('outside scope\\n', encoding='utf-8'); "
                "print('updated docs')"
            ),
            "--prompt",
            "edit the docs",
            "--json",
        ],
    )

    assert result.exit_code == 3
    assert '"Path policy violation detected:' in result.stdout
    assert '"docs/runbook.md is outside the editable scope for implementer."' in result.stdout

    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"current_state": "blocked"' in status_result.stdout


def test_agent_run_transitions_to_validation_when_scope_is_allowed(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_committed_repo(repository_root)
    assert runner.invoke(app, ["init", str(repository_root), "--write"]).exit_code == 0
    assert runner.invoke(app, ["task", "create", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["plan", "TASK-001", str(repository_root)]).exit_code == 0
    assert runner.invoke(app, ["approve-plan", "TASK-001", str(repository_root)]).exit_code == 0

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
            (
                "from pathlib import Path; "
                "Path('src/notes.txt').parent.mkdir(parents=True, exist_ok=True); "
                "Path('src/notes.txt').write_text('allowed change\\n', encoding='utf-8'); "
                "print('updated src')"
            ),
            "--prompt",
            "edit the source",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert '"changed_files": [' in result.stdout
    assert '"src/notes.txt"' in result.stdout

    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"current_state": "validating"' in status_result.stdout