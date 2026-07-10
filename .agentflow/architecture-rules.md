# Architecture Rules

- The orchestrator owns workflow state transitions.
- Agents are bounded workers behind adapters.
- Deterministic validation runs before reviewer analysis.
- Git worktrees isolate implementation.
- Project-local files remain inspectable and human-readable.
- Avoid speculative abstractions that do not support the next implementation slice.
