# AgentFlow User Guide

This guide explains how to install AgentFlow, initialize a repository, run tasks through the workflow, use every command group, and understand where core behavior is implemented.

## 1. What AgentFlow Does

AgentFlow is a local-first orchestration CLI for AI-assisted software delivery.

- AgentFlow controls workflow state and approvals.
- Adapters run bounded agent jobs.
- Git and task artifacts provide inspectable evidence.
- Policies constrain commands and file edits by role.

## 2. Prerequisites

- Linux, macOS, or Windows shell environment
- Git available on PATH
- Python 3.12+

Verify:

```bash
python --version
git --version
```

## 3. Install and Development Setup

From repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
agentflow --help
```

Optional quality checks:

```bash
pytest
ruff check .
mypy src
```

## 4. Initialize a Target Repository

AgentFlow operates inside an existing Git repository.

Preview initialization:

```bash
agentflow init /path/to/repo
```

Write files:

```bash
agentflow init /path/to/repo --write
```

Add optional VS Code tasks:

```bash
agentflow init /path/to/repo --write --vscode-tasks
```

Then verify Copilot CLI connectivity:

```bash
agentflow doctor-copilot --prompt "Reply with exactly: OK"
```

`doctor-copilot` uses `claude-haiku-4.5` by default to keep credit usage low. Override with `--model` when needed.

Generated core files include:

- .agentflow/config.yaml
- .agentflow/validation.yaml
- .agentflow/policies/commands.yaml
- .agentflow/policies/paths.yaml
- .agentflow/tasks/.gitkeep

## 5. Command Reference

### 5.1 Project and Configuration

```bash
agentflow version
agentflow doctor [PATH] [--json]
agentflow doctor-copilot [--prompt "..."] [--model MODEL] [--timeout 60] [--json]
agentflow project inspect [PATH] [--json]
agentflow config show [PATH] [--json]
agentflow config show [PATH] --resolved [--task-id TASK-001] [--json]
```

After `agentflow init`, run `agentflow doctor-copilot` to verify that the Copilot CLI is installed and can answer a prompt.

### 5.2 Task Records and State

```bash
agentflow task create TASK-001 [PATH] [--title "..."] [--json]
agentflow task list [PATH] [--json]
agentflow task show TASK-001 [PATH] [--json]
agentflow task status TASK-001 [PATH] [--json]
agentflow events TASK-001 [PATH] [--json]
```

### 5.3 Planning and State Transitions

```bash
agentflow plan TASK-001 [PATH] [--adapter fake|subprocess-text|copilot-cli] [--command ...] [--json]
agentflow approve-plan TASK-001 [PATH] [--reason "..."] [--json]
agentflow reject-plan TASK-001 [PATH] [--reason "..."] [--json]
agentflow block TASK-001 [PATH] [--reason "..."] [--json]
agentflow resume TASK-001 --to planning|implementing|cancelled [PATH] [--reason "..."] [--json]
```

### 5.4 Agent and Command Execution

```bash
agentflow agent-run TASK-001 --role planner|implementer|tester|reviewer|documenter --prompt "..." [PATH] [--adapter ...] [--command ...] [--json]
agentflow command-run TASK-001 [PATH] --command <token> --command <token> ... [--json]
agentflow approve-command TASK-001 [PATH] [--json]
agentflow reject-command TASK-001 [PATH] [--json]
```

For GitHub Copilot CLI, install it first and then use the dedicated adapter name:

```bash
npm install -g @github/copilot
brew install --cask copilot-cli
curl -fsSL https://gh.io/copilot-install | bash

agentflow agent-run TASK-001 --role implementer --adapter copilot-cli --command copilot --command --prompt --prompt "Refactor this module" --json
```

The first `--prompt` above is the Copilot CLI flag. The second `--prompt` is the AgentFlow prompt passed to the adapter.

When `--adapter copilot-cli` is used and no model flag is present in command tokens, AgentFlow injects `--model claude-haiku-4.5` by default.

### 5.5 Validation, Review, and Run Loop

```bash
agentflow validate TASK-001 [PATH] [--json]
agentflow review TASK-001 [PATH] [--adapter ...] [--command ...] [--json]
agentflow run TASK-001 [PATH] [--adapter ...] [--command ...] [--with-tester] [--with-docs] [--json]
```

### 5.6 Slice 17 and 18 Optional Commands

```bash
agentflow document TASK-001 [PATH] [--adapter ...] [--command ...] [--prompt "..."] [--json]
agentflow test-agent TASK-001 [PATH] [--adapter ...] [--command ...] [--prompt "..."] [--json]
```

### 5.7 Finalization

```bash
agentflow approve-commit TASK-001 [PATH] [--message "..."] [--json]
```

## 6. Recommended End-to-End Workflow

1. Initialize repository and create task.

```bash
agentflow init . --write
agentflow task create TASK-001 --title "Implement feature X"
```

2. Plan and approve.

```bash
agentflow plan TASK-001
agentflow approve-plan TASK-001 --reason "Plan is good"
```

3. Run the bounded loop.

```bash
agentflow run TASK-001 --with-tester --with-docs
```

4. Inspect state and evidence.

```bash
agentflow task status TASK-001 --json
agentflow events TASK-001 --json
```

5. Approve final commit when ready.

```bash
agentflow approve-commit TASK-001 --message "TASK-001: complete"
```

## 7. Policy and Safety Model

- Command policy: .agentflow/policies/commands.yaml
- Path policy: .agentflow/policies/paths.yaml
- Role-based path scope is enforced on changed files after each agent run.
- Violations block progression and persist violation artifacts.
- Dangerous patterns are blocked by command policy.

## 8. Task Artifacts You Should Expect

Per task under .agentflow/tasks/TASK-001:

- task.yaml and state.json
- events.jsonl
- plan.md
- validation-results.json and validation logs
- findings.json and review-result.json
- runs/*.json for agent execution records
- documentation-result.json after document command
- tester-result.json after test-agent command

## 9. Exit Codes You Will Commonly See

- 0: successful command
- 1: validation or usage error for command preconditions
- 3: path policy violation during agent/document/tester execution
- 4: command-run requires approval
- 6: validate or review reported failure/rejection
- 7: run flow ended blocked

## 10. Troubleshooting

- Not in repo error:
  Run commands inside a Git repository.
- Not initialized error:
  Run agentflow init --write first.
- Path policy violations:
  Adjust role-scoped paths in .agentflow/policies/paths.yaml or change the role/intent.
- Command blocked:
  Check .agentflow/policies/commands.yaml and blocked patterns.
- Unexpected state-transition error:
  Use agentflow task status TASK-001 --json and verify allowed_transitions.

## 11. Where the Magic Happens in Code

Primary command surface:

- src/agentflow/cli/main.py

Core orchestration services:

- src/agentflow/application/run_flow.py
- src/agentflow/application/planning.py
- src/agentflow/application/validation.py
- src/agentflow/application/review.py
- src/agentflow/application/finalization.py

Slice 17 and 18 services:

- src/agentflow/application/documentation.py
- src/agentflow/application/tester.py

Safety and enforcement:

- src/agentflow/application/path_policy.py
- src/agentflow/application/command_runner.py
- src/agentflow/application/state_transitions.py

Persistence and evidence:

- src/agentflow/application/task_records.py
- src/agentflow/application/task_events.py

Adapters:

- src/agentflow/adapters/fake.py
- src/agentflow/adapters/subprocess_text.py

## 12. Fast Start Cheat Sheet

```bash
agentflow init . --write
agentflow task create TASK-001 --title "My task"
agentflow plan TASK-001
agentflow approve-plan TASK-001
agentflow run TASK-001 --with-tester --with-docs
agentflow approve-commit TASK-001
```
