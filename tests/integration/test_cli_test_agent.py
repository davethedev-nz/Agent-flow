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


def _create_task(repository_root: Path) -> None:
    repository_root.mkdir(parents=True)
    _run_git(repository_root, "init", "-b", "main")
    _run_git(repository_root, "config", "user.email", "test@example.com")
    _run_git(repository_root, "config", "user.name", "Test User")
    (repository_root / "src").mkdir()
    (repository_root / "tests").mkdir()
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


def test_test_agent_can_update_test_paths(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_task(repository_root)
    _write_state(repository_root, "code_review")

    result = runner.invoke(
        app,
        [
            "test-agent",
            "TASK-001",
            str(repository_root),
            "--adapter",
            "subprocess-text",
            "--command",
            sys.executable,
            "--command",
            "-c",
            "--command",
            (
                "from pathlib import Path; "
                "Path('tests/test_slice18.py').write_text('def test_ok():\\n    assert True\\n', encoding='utf-8'); "
                "print('tests updated')"
            ),
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert '"role": "tester"' in result.stdout
    assert '"tests/test_slice18.py"' in result.stdout
    assert (repository_root / ".agentflow" / "tasks" / "TASK-001" / "tester-result.json").exists()


def test_test_agent_blocks_when_editing_source_code(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _create_task(repository_root)
    _write_state(repository_root, "code_review")

    result = runner.invoke(
        app,
        [
            "test-agent",
            "TASK-001",
            str(repository_root),
            "--adapter",
            "subprocess-text",
            "--command",
            sys.executable,
            "--command",
            "-c",
            "--command",
            (
                "from pathlib import Path; "
                "Path('src/unsafe.py').parent.mkdir(parents=True, exist_ok=True); "
                "Path('src/unsafe.py').write_text('print(1)\\n', encoding='utf-8'); "
                "print('bad scope')"
            ),
            "--json",
        ],
    )

    assert result.exit_code == 3
    assert '"Path policy violation detected:' in result.stdout
    assert '"src/unsafe.py is outside the editable scope for tester."' in result.stdout
    status_result = runner.invoke(app, ["task", "status", "TASK-001", str(repository_root), "--json"])
    assert status_result.exit_code == 0
    assert '"current_state": "blocked"' in status_result.stdout