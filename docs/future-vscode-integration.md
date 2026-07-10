# Future VS Code Integration

## Position

The VS Code extension is a future view and interaction layer. It must not own orchestration logic.

## MVP integration path

- stable CLI commands
- repository-local visible artifacts
- optional `.vscode/tasks.json` templates
- separate worktrees opened in normal VS Code windows
- Markdown and JSON outputs that are easy to inspect

## Future extension responsibilities

- show current project and task
- render workflow state and pending approvals
- display recent events, findings, and validation results
- open context packs, plans, and completion reports
- trigger existing CLI commands

## Extension non-responsibilities

- no workflow state machine logic
- no provider adapter logic
- no hidden task persistence model
- no alternate approval store

## API direction

Design application services and CLI output so the extension can later consume:

- `agentflow status --json`
- `agentflow events --json`
- `agentflow findings --json`
- `agentflow context show --json`
- `agentflow config show --resolved --json`
