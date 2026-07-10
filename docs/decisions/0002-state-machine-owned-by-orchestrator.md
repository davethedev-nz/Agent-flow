# ADR 0002: State Machine Owned By Orchestrator

## Status

Accepted

## Context

Agents should not own workflow state or decide arbitrary transitions.

## Decision

The orchestrator is the only component allowed to mutate task state after validating transitions and persisting events.

## Consequences

- Safer resumability and auditability
- Clear separation between advisory agent output and authoritative workflow control
- Slightly more orchestration code, but less hidden behavior
