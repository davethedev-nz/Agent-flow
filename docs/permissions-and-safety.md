# Permissions And Safety

## Safety model

Prompt instructions are not enough. AgentFlow must verify path and command restrictions outside the model.

## Path controls

Support:

- allowed path patterns
- forbidden paths
- read-only paths
- role-specific editable roots

Validation runs after every agent execution:

1. collect changed files
2. normalize to repository-relative paths
3. evaluate against allow and deny rules
4. block or require human intervention on violations

## Command controls

Support:

- executable allowlist
- forbidden command patterns
- argument validation rules
- one-time approvals
- task-level approvals
- timeouts
- output-size limits
- environment-variable filtering

## Commands that must be blocked or gated

- `sudo`
- `su`
- `rm -rf`
- destructive `find -delete`
- `git push`
- `git reset --hard`
- `git clean -fd`
- force-push variants
- `terraform apply`
- `terraform destroy`
- destructive cloud commands
- destructive Kubernetes commands
- database drop or truncate operations
- production deployment commands

## Shell safety

The command runner should prefer subprocess invocation without a shell:

- pass argv arrays, not shell strings
- reject metacharacters in agent-requested command text unless explicitly routed through a reviewed shell wrapper
- parse and validate executable plus arguments separately

## Approval model

Recommended human gates:

- plan approval
- scope expansion approval
- destructive or infrastructure command approval
- final commit approval
- future push or PR approval

Default behavior should not ask for approval on every small code edit.

## Secret and credential protection

Practical MVP controls:

- mark common secret files and directories as forbidden by default
- filter selected environment variables before subprocess execution
- cap raw output persistence size
- persist logs to files with predictable location and access boundaries

## Verification after agent runs

After each agent execution, the orchestrator must verify:

- allowed paths only
- no blocked commands were run
- requested commands are recorded
- output schema validates
- no validator evidence was silently modified

## Future extensions

- network policy
- per-role filesystem sandboxing
- OS-level syscall restriction
- stronger secret scanning and credential redaction
