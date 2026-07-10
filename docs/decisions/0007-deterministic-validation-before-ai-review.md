# ADR 0007: Deterministic Validation Before AI Review

## Status

Accepted

## Context

Review agents should not infer facts that scripts can prove more reliably.

## Decision

Run deterministic validators before reviewer analysis and persist structured evidence for the reviewer.

## Consequences

- Higher confidence review inputs
- Better separation of objective failures from subjective findings
- Requires a structured validation-pipeline model
