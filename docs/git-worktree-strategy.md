# Git Worktree Strategy

## Goals

- isolate task work from the main working copy
- keep evidence in Git
- let the orchestrator own integration
- allow recovery after failure or interruption

## MVP model

- one integration branch per task: `task/<task-id>`
- one implementation worktree per task
- no direct push from agents
- the orchestrator creates, inspects, and cleans worktrees

## Lifecycle

1. Task created.
2. Plan approved.
3. Orchestrator creates branch `task/TASK-001` from selected base branch.
4. Orchestrator creates a worktree under a managed path.
5. Implementer works only inside that worktree.
6. Validation and review run against the worktree state.
7. Final human approval allows a local commit on the integration branch.
8. Task completion permits optional worktree cleanup.

## Managed paths

A user-level workspace store is preferable for worktree metadata. Actual worktrees may live under:

```text
~/.local/share/agentflow/worktrees/<project-id>/<task-id>/
```

The exact location should be configurable.

## Service contract

The worktree service must provide:

- ensure branch exists
- create or reuse worktree idempotently
- inspect current branch, HEAD, and dirty state
- detect detached or corrupted state
- remove abandoned worktrees safely

## Checkpoints and commits

### Checkpoint commits

Not required in early slices. Prefer explicit artifact persistence first. Later, optional checkpoint commits may help long repair loops.

### Final commit

Only after:

- path policy passes
- validation pipeline passes
- reviewer approves or no blocking findings remain
- human final approval is recorded

## Specialist branches

Future versions may add:

- `task/TASK-001-implementation`
- `task/TASK-001-tests`
- `task/TASK-001-docs`

The orchestrator remains responsible for cherry-picking or otherwise integrating specialist output.

## Failure handling

Detect and log:

- dirty worktree before agent run
- changes outside allowed paths after agent run
- missing branch
- detached HEAD
- failed branch creation
- merge or cherry-pick conflicts in future specialist flows

## Recovery

On resume:

- locate existing worktree by task metadata
- confirm branch and root paths
- detect uncommitted changes
- compare changed files with allowed scope
- continue from the last safe state or mark blocked if ambiguous
