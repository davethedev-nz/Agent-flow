# Testing Strategy

## Goals

- prove the state machine rules
- prove config resolution and idempotent init
- prove safety restrictions independent of prompts
- avoid paid provider access

## Test layers

### Unit tests

- state transition validation
- configuration merge rules
- path policy evaluation
- command policy parsing and validation
- validation result parsing
- finding identity stability
- non-progress detection

### Integration tests

- repository-root discovery
- project detection
- safe and idempotent `agentflow init`
- worktree lifecycle in temp repos
- interrupted process recovery
- event log and snapshot reconciliation
- CLI flows for create, plan, approve, run, block, resume

### Adapter contract tests

Use fake providers and golden malformed outputs to verify:

- structured output parsing
- timeout handling
- partial output persistence
- schema validation failures

## Test doubles

Required fakes:

- fake agent adapter
- fake Git service
- fake worktree service
- fake command runner
- fake clock

## Real temporary repository tests

Use temp directories with real Git repositories for:

- root discovery
- init behavior
- path policy checks against changed files
- worktree creation and cleanup

## MVP acceptance test emphasis

Highest-value early tests:

- installable CLI command smoke test
- repository discovery test
- init preview and no-overwrite test
- task creation persistence test
- state transition validator test
- event append and recovery test
