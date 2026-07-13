# CLI Design

## Goals

- work well in the VS Code integrated terminal
- provide Rich human output and JSON for automation
- make approval boundaries explicit
- keep commands scriptable and debuggable

## Command groups

```bash
agentflow init
agentflow doctor
agentflow doctor-copilot
agentflow project inspect
agentflow config show
agentflow config show --resolved

agentflow task create TASK-001
agentflow task list
agentflow task show TASK-001
agentflow task cancel TASK-001
agentflow task archive TASK-001

agentflow plan TASK-001
agentflow approve-plan TASK-001
agentflow reject-plan TASK-001

agentflow run TASK-001
agentflow validate TASK-001
agentflow review TASK-001
agentflow repair TASK-001

agentflow status TASK-001
agentflow events TASK-001
agentflow findings TASK-001
agentflow context show TASK-001

agentflow approve-command TASK-001
agentflow reject-command TASK-001

agentflow approve-commit TASK-001
agentflow block TASK-001
agentflow resume TASK-001
```

## Command principles

- commands should map to workflow boundaries
- every mutating command should persist an event
- commands should return meaningful exit codes
- `--json` should produce stable machine-readable payloads
- `--debug` should expose provider output and raw log locations

## Example session: project initialization

```text
$ agentflow init
Detected repository root: /repo
Detected stack: python
Proposed source paths: src/, tests/
Proposed validation commands: ruff check ., mypy src, pytest
Write .agentflow files? [y/N]: y
Initialized AgentFlow project config.

$ agentflow doctor-copilot
Copilot CLI responded successfully.
```

## Example session: successful task completion

```text
$ agentflow task create TASK-001
Created task TASK-001 in state created.

$ agentflow plan TASK-001
Planner run complete. Task moved to plan_review.

$ agentflow approve-plan TASK-001
Plan approved. Worktree ready for implementation.

$ agentflow run TASK-001
Implementation completed. Validation passed. Review approved.
Task moved to final_review.

$ agentflow approve-commit TASK-001
Created local commit on task/TASK-001.
Task complete.
```

## Example session: rejected plan

```text
$ agentflow plan TASK-002
Planner run complete. Task moved to plan_review.

$ agentflow reject-plan TASK-002 --reason "Missing migration plan"
Plan rejected. Task returned to planning.
```

## Example session: validation failure and repair

```text
$ agentflow run TASK-003
Validation failed in validator tests.
Task moved to repairing.

$ agentflow repair TASK-003
Repair iteration 2 complete.
Validation passed. Review pending.
```

## Example session: blocked task

```text
$ agentflow run TASK-004
Blocked: changed file outside allowed scope docs/ops/runbook.md
Use `agentflow status TASK-004` for details.
```

## Example session: command approval request

```text
$ agentflow run TASK-005
Approval required for command: terraform plan
Use `agentflow approve-command TASK-005` or `agentflow reject-command TASK-005`.
```

## Example session: resume after interruption

```text
$ agentflow resume TASK-006
Recovered interrupted implementer run.
Last safe state: implementing
Pending validation: yes
Task resumed.
```

## Suggested exit codes

- `0`: success
- `2`: invalid usage
- `3`: policy violation
- `4`: approval required
- `5`: provider failure
- `6`: validation failure
- `7`: blocked task
- `8`: persistence or recovery error
