# Agent Contracts

## Contract goals

- provider-neutral execution
- strict role boundaries
- bounded context and permissions
- schema-validated outputs
- inspectable raw transcripts and normalized results

## Common request schema

Every adapter receives an `AgentRequest` with:

- task ID
- role
- prompt body
- working directory
- repository root
- allowed paths
- forbidden paths
- allowed commands
- forbidden command patterns
- context files
- iteration number
- timeout
- maximum output size
- expected output schema
- environment restrictions
- task-specific instructions

## Common result schema

Every adapter returns an `AgentResult` with:

- success status
- provider name
- model identifier when available
- role
- summary
- changed files
- commands requested
- commands run
- findings
- structured output
- raw output location
- exit code
- start and finish timestamps
- duration
- timeout flag
- usage metadata
- cost metadata
- schema validation status

## Role contracts

### Planner

Allowed:

- inspect bounded repository context
- propose implementation plan
- propose validation commands
- identify affected areas, risks, assumptions, and unknowns

Forbidden:

- code edits
- commits
- workflow transitions
- acceptance-criteria changes
- arbitrary command execution

Required output:

- plan summary
- proposed steps
- affected areas
- acceptance-criteria mapping
- risks
- assumptions
- unresolved questions
- proposed validation commands
- proposed path scope

### Implementer

Allowed:

- edit approved paths
- run approved development commands
- address approved plan and unresolved findings

Forbidden:

- edits outside allowed scope
- unapproved commits
- pushes
- unrelated refactors
- acceptance-criteria changes
- silent scope expansion

Required output:

- summary
- changed files
- commands requested
- commands run
- assumptions
- unresolved concerns
- findings addressed
- findings not addressed
- suggested next state

### Tester

Allowed:

- add or improve tests in permitted test paths
- run approved validation commands
- identify untested conditions

Forbidden:

- repair production code
- weaken assertions
- remove failing tests to force pass
- alter acceptance criteria

Required output:

- tests added or changed
- criteria covered
- criteria not covered
- commands run
- failures
- coverage concerns
- recommendations

### Reviewer

Allowed:

- read-only diff review
- compare output to approved plan and acceptance criteria
- inspect deterministic validation evidence

Forbidden:

- file edits
- commits
- workflow transitions
- unapproved command execution

Required output:

- verdict: `approved`, `rejected`, or `blocked`
- structured findings
- summary rationale

### Documenter

Allowed:

- update documentation paths only
- reflect validated final behavior

Forbidden:

- source-code changes unless separately approved
- speculative documentation from unimplemented plans

Required output:

- documentation changed
- documentation still required
- public behavior documented
- deployment or configuration impact documented
- unresolved concerns

## Provider handling strategy

### Structured-output providers

Use the provider-native format when available, then validate against the Pydantic schema.

### Text-only providers

Wrap prompts with an explicit JSON or YAML schema requirement. Parse, validate, and reject malformed responses.

### Malformed or partial output

- persist raw output
- mark run failed
- record parsing error and failure signature
- allow bounded retry or human intervention based on policy

### Timeouts and interruptions

- terminate child process when possible
- record timeout in metadata
- persist partial output safely
- return task to the last safe orchestration boundary

### Authentication or provider failures

Treat as infrastructure failure, not task success or review evidence. Record the failure event and allow retry or provider switch.
