# AgentFlow

AgentFlow is a local-first, controlled, inspectable, resumable AI software-development orchestration tool.

The product goal is simple:

> AgentFlow owns the workflow. Agents perform bounded jobs. Git owns the evidence. The developer approves important transitions.

This repository contains the initial architecture, product design, implementation roadmap, and a thin Python scaffold for the installable `agentflow` tool. It does **not** implement the full orchestration product yet.

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

## Planned CLI

```bash
agentflow init
agentflow doctor
agentflow project inspect
agentflow config show --resolved

agentflow task create TASK-001
agentflow plan TASK-001
agentflow approve-plan TASK-001
agentflow run TASK-001
agentflow validate TASK-001
agentflow review TASK-001
agentflow repair TASK-001
agentflow approve-commit TASK-001
```

## Current status

The current code is intentionally thin. It defines package boundaries, interfaces, schemas, example templates, and a basic CLI entry point so implementation can proceed in small vertical slices.

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
