# ADR 0004: Git Worktree Isolation

## Status

Accepted

## Context

Implementation should be isolated from the developer's main working copy while preserving local Git evidence.

## Decision

Use one integration branch and one implementation worktree per task in the MVP.

## Consequences

- Clear task isolation
- Good fit for future specialist branches
- More Git lifecycle handling is required in orchestration
