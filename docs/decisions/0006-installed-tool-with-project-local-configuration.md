# ADR 0006: Installed Tool With Project-local Configuration

## Status

Accepted

## Context

AgentFlow must operate across unrelated repositories without copying its full source tree into each one.

## Decision

Distribute AgentFlow as an installed tool and write only project-facing configuration and task artifacts into target repositories.

## Consequences

- Cleaner product boundaries
- Easier upgrades of the installed tool
- Requires a strong init flow and configuration-resolution model
