# ADR 0003: Agent Provider Adapters

## Status

Accepted

## Context

The product must remain replaceable across model providers and local CLIs.

## Decision

Define a provider-neutral adapter interface around `AgentRequest` and `AgentResult`, with provider-specific implementations behind it.

## Consequences

- Reduced lock-in
- Easier testing through fake adapters
- Requires explicit normalization and schema-validation logic
