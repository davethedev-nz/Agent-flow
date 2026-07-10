from __future__ import annotations

from datetime import UTC, datetime

from agentflow.domain.models import AgentExecutionMetadata, AgentRequest, AgentResult


class FakeAgentAdapter:
    provider_name = "fake"

    def execute(self, request: AgentRequest) -> AgentResult:
        started_at = datetime.now(UTC)
        finished_at = datetime.now(UTC)
        return AgentResult(
            success=True,
            provider=self.provider_name,
            role=request.role,
            summary=f"Fake {request.role.value} run completed.",
            structured_output={
                "prompt_excerpt": request.prompt[:200],
                "context_files": [str(path) for path in request.context_files],
            },
            metadata=AgentExecutionMetadata(
                provider=self.provider_name,
                model="fake-static",
                exit_code=0,
                started_at=started_at,
                finished_at=finished_at,
                duration_seconds=(finished_at - started_at).total_seconds(),
                timeout=False,
            ),
        )
