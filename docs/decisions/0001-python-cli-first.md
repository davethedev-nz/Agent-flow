# ADR 0001: Python CLI First

## Status

Accepted

## Context

The first delivery needs to be installable, scriptable, usable from VS Code, and maintainable by one developer.

## Decision

Build AgentFlow first as a Python CLI using Typer and Rich.

## Consequences

- Faster delivery of an inspectable MVP
- Simple integration with Git, subprocess-based providers, and local files
- Future VS Code and web interfaces can wrap stable application services and CLI contracts
