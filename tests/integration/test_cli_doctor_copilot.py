from __future__ import annotations

import subprocess

import pytest
from typer.testing import CliRunner

from agentflow.cli.main import app

runner = CliRunner()


def test_doctor_copilot_uses_installed_cli_and_returns_response(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr("agentflow.cli.main.shutil.which", lambda name: "/usr/bin/copilot" if name == "copilot" else None)

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="OK\n", stderr="")

    monkeypatch.setattr("agentflow.cli.main.subprocess.run", fake_run)

    result = runner.invoke(app, ["doctor-copilot", "--prompt", "Reply with exactly: OK", "--json"])

    assert result.exit_code == 0
    assert calls == [["/usr/bin/copilot", "--model", "claude-haiku-4.5", "--prompt", "Reply with exactly: OK"]]
    assert '"status": "ok"' in result.stdout
    assert '"model": "claude-haiku-4.5"' in result.stdout
    assert '"stdout": "OK"' in result.stdout


def test_doctor_copilot_fails_when_cli_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("agentflow.cli.main.shutil.which", lambda name: None)

    result = runner.invoke(app, ["doctor-copilot", "--json"])

    assert result.exit_code == 1
    assert '"copilot CLI is not installed or not on PATH."' in result.stdout