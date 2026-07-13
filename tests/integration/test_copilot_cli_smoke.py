from __future__ import annotations

import shutil
import subprocess

import pytest


def test_copilot_cli_responds_to_help() -> None:
    copilot = shutil.which("copilot")
    if copilot is None:
        pytest.skip("copilot CLI is not installed on this machine")

    completed = subprocess.run(
        [copilot, "help"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode == 0
    output = (completed.stdout + completed.stderr).strip()
    assert output
    assert "Copilot" in output or "Usage" in output