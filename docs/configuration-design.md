# Configuration Design

## Resolution model

Configuration is resolved from four layers:

1. built-in defaults
2. user-level config
3. project-level config
4. task-level overrides

Every resolved setting must retain its origin.

## Main config files

### User-level

Example location:

```text
~/.config/agentflow/config.yaml
```

Contents may include:

- default provider preference
- default worktree root
- default output format
- global blocked command patterns

### Project-level

Stored at `.agentflow/config.yaml`.

Example:

```yaml
schema_version: 1
project:
  id: agentflow-self
  stack_profiles: [python]
paths:
  source: [src]
  tests: [tests]
  documentation: [docs]
  infrastructure: []
  forbidden: [.venv, dist, .git]
autonomy:
  plan_requires_approval: true
  code_edits_require_approval: false
  scope_expansion_requires_approval: true
  command_approval_mode: allowlist
  maximum_repair_iterations: 4
  commit_requires_approval: true
  push_allowed: false
efficiency:
  prefer_minimal_context: true
  max_context_files: 12
  max_context_file_bytes: 80000
  max_prompt_chars: 24000
  require_diff_scoped_repair_context: true
  summarize_large_logs: true
providers:
  planner: builtin-text-adapter
  implementer: builtin-text-adapter
```

### Task-level overrides

Stored in task metadata and used sparingly for:

- narrower path scope
- temporary command approvals
- reduced repair limit
- task-specific provider choice

## Merge semantics

- mappings merge recursively unless explicitly replaced
- lists default to replace unless the setting supports additive merge
- prompt overrides may specify `mode: extend` or `mode: replace`

## Resolved output

`agentflow config show --resolved` should display both value and origin, optionally with full JSON.

## Profiles

Built-in profiles help `agentflow init` propose defaults:

- `python`
- `django`
- `node-typescript`
- `.net`
- `terraform`
- `monorepo-mixed`

Profiles are templates, not hidden magic. The generated config remains explicit and editable.

## Efficiency defaults

AgentFlow should minimize token use by default instead of relying on ad hoc prompt discipline.

- prefer narrow context packs over broad repository dumps
- cap the number and size of selected context files
- cap prompt size before dispatching to an agent
- restrict repair iterations to unresolved findings and relevant diff slices
- summarize large validator logs before including them in prompts

These settings belong in configuration so projects can tighten or relax them explicitly.
