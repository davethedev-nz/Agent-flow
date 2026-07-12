# AgentFlow

AgentFlow is a local-first, controlled, inspectable, resumable AI software-development orchestration tool.

The product goal is simple:

> AgentFlow owns the workflow. Agents perform bounded jobs. Git owns the evidence. The developer approves important transitions.

This repository contains architecture and product docs plus a working Python implementation of the core orchestration loop through slice 15.

## What is in this repository

- Architecture and product documentation in `docs/`
- Architecture decision records in `docs/decisions/`
- A minimal Python package scaffold in `src/agentflow/`
- Test layout and fixtures for incremental implementation
- Example project configuration and task artifacts in `examples/`
- A self-hosted `.agentflow/` folder showing how AgentFlow configures a target repository

## Design constraints

- Local-first and inspectable
- Provider-neutral agent adapters
- Explicit workflow state machine
- Deterministic validation before AI review
- Human approval at meaningful boundaries
- Safe interruption and resume
- Reusable across many unrelated Git repositories

## Current CLI

```bash
agentflow init
agentflow doctor
agentflow project inspect
agentflow config show --resolved

agentflow task create TASK-001
agentflow task list
agentflow task show TASK-001
agentflow task status TASK-001
agentflow events TASK-001

agentflow plan TASK-001
agentflow approve-plan TASK-001
agentflow reject-plan TASK-001
agentflow agent-run TASK-001 --role implementer --prompt "..."

agentflow command-run TASK-001 --command git --command status
agentflow approve-command TASK-001
agentflow reject-command TASK-001

agentflow validate TASK-001
agentflow review TASK-001
agentflow run TASK-001
agentflow block TASK-001
agentflow resume TASK-001 --to planning
agentflow approve-commit TASK-001
```

## Current status

Slices 1 through 15 are implemented on this feature branch, including:

- repository discovery and safe initialization
- task persistence, transitions, events, and worktrees
- provider-neutral agent execution
- command and path policy enforcement
- deterministic validation and reviewer findings
- bounded repair loop orchestration
- final approval with local completion commit
- optional VS Code task examples during init
- optional documentation pass constrained to documentation paths
- optional tester-agent workflow constrained to test paths

Roadmap slices 1 through 18 are implemented on this branch.

## Development

Target stack:

- Python 3.12+
- Typer
- Pydantic v2
- Rich
- PyYAML
- pytest
- Ruff
- mypy

Example local commands:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
agentflow --help
pytest
ruff check .
mypy src
```

## License

MIT
