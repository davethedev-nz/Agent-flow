# Persistence Design

## Source of truth strategy

Use a hybrid model:

- repository-local human-readable files are the source of truth for project config and task artifacts
- append-only event logs provide auditability and recovery evidence
- user-level SQLite stores indexes, queryable run metadata, approvals, and cost data

## Repository-local structure

```text
.agentflow/
├── config.yaml
├── project-context.md
├── architecture-rules.md
├── validation.yaml
├── policies/
├── prompts/
└── tasks/
    └── TASK-001/
        ├── task.yaml
        ├── requirements.md
        ├── acceptance-criteria.md
        ├── plan.md
        ├── state.json
        ├── context/
        ├── runs/
        ├── events.jsonl
        ├── findings.json
        ├── validation-results.json
        ├── approvals.json
        └── completion.md
```

## File placement rationale

### Human-readable and Git-trackable

- requirements
- acceptance criteria
- plan
- project guidance
- prompt overrides
- completion report

These are portable, reviewable, and useful in code review.

### Human-readable but commonly ignored

- run logs
- large raw provider output
- validator logs
- context pack copies when large

These can live under the task directory but may be ignored via `.gitignore` depending on team preference.

### SQLite

Use a user-level SQLite database for:

- project registry
- task discovery across repositories
- event and run indexes
- approvals index
- provider usage and cost metadata
- quick dashboard queries later

## Trade-offs

Files are transparent and portable, but slower for global queries. SQLite is efficient for cross-project inspection, but not ideal as the only durable store for repository-local workflow state. The hybrid approach preserves inspectability without sacrificing future querying.

## Atomicity

- write JSON and YAML through temp files and atomic rename
- append events with line-buffered fsync-aware writes where appropriate
- never partially overwrite task state in place

## Schema versioning

- include `schema_version` in all durable JSON and YAML structures
- define migrations for both file artifacts and SQLite tables
- keep migrations explicit and reversible where possible

## Corruption handling

- validate snapshots on load
- reconcile snapshots against events
- back up invalid files before repair
- block the task if the durable record cannot be trusted automatically

## Cloned repositories and multiple worktrees

Task state remains repository-local, so clones naturally isolate task histories. Multiple worktrees of the same repository root must refer back to the same `.agentflow` directory and project identity.
