from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

from agentflow.domain.models import AgentExecutionMetadata, AgentRequest, AgentResult


class SubprocessTextAgentAdapter:
    provider_name = "subprocess-text"

    def __init__(self, command: list[str]) -> None:
        if not command:
            raise ValueError("A subprocess-text adapter requires at least one command token.")
        self._command = command

    def execute(self, request: AgentRequest) -> AgentResult:
        started_at = datetime.now(UTC)
        completed = subprocess.run(
            [*self._command, request.prompt],
            cwd=request.working_directory,
            capture_output=True,
            text=True,
            timeout=request.timeout_seconds,
            check=False,
        )
        finished_at = datetime.now(UTC)
        raw_output_path = request.working_directory / ".agentflow" / "tmp-subprocess-output.txt"
        raw_output_path.write_text(completed.stdout, encoding="utf-8")
        return AgentResult(
            success=completed.returncode == 0,
            provider=self.provider_name,
            role=request.role,
            summary=completed.stdout.strip() or "Subprocess adapter completed.",
            commands_run=[" ".join([*self._command, request.prompt])],
            structured_output={"stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()},
            raw_output_location=raw_output_path,
            metadata=AgentExecutionMetadata(
                provider=self.provider_name,
                model=None,
                exit_code=completed.returncode,
                started_at=started_at,
                finished_at=finished_at,
                duration_seconds=(finished_at - started_at).total_seconds(),
                timeout=False,
            ),
        )
