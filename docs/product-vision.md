# Product Vision

## Purpose

AgentFlow is an installable developer tool for orchestrating AI-assisted software work inside existing Git repositories without surrendering workflow control to model providers.

The product is designed for one developer first. It should be small enough to understand, safe enough to trust, and explicit enough to inspect when it fails.

## Core principle

```text
AgentFlow owns the workflow.
Agents perform bounded jobs.
Git owns the evidence.
The developer approves important transitions.
```

## Product goals

- Operate as a reusable tool across many unrelated repositories.
- Persist workflow state outside agent conversations.
- Keep orchestration logic separate from IDE presentation.
- Constrain agents by role, path policy, command policy, and schema validation.
- Prefer deterministic proof over AI judgment when proof is available.
- Resume safely after interruption.
- Remain provider-neutral and locally operable.

## Target user

A developer who wants help planning, implementing, validating, and reviewing changes, but does not want an agent to silently redefine scope, bypass Git evidence, or declare work complete without explicit checks.

## Product boundaries

### Included in MVP

- Python CLI
- Repository initialization for existing Git repositories
- Project-local configuration
- Task records and workflow state machine
- Provider-neutral agent adapter contract
- One planner adapter and one implementer adapter
- Deterministic validation pipeline
- Read-only reviewer
- Bounded repair loop
- Final human-approved local commit

### Excluded from MVP

- Parallel specialist agents
- Cloud execution
- Automatic pushes or PR creation
- Full VS Code extension
- Web dashboard
- Embeddings or semantic indexing
- Multi-user collaboration
- Deployment automation

## Product layers

1. AgentFlow product: installable package, defaults, orchestration, adapters, validation, templates.
2. Project integration: repository-local configuration, rules, prompts, task records, VS Code task examples.
3. Task records: persisted requirements, plan, state, events, validation evidence, findings, approvals.

## Success criteria

A developer can install AgentFlow, run `agentflow init` inside an existing repository, create a task, approve a plan, run bounded implementation and review loops, inspect evidence from VS Code, and finish with a human-approved local commit.

## Design principles

- Clarity over automation theater
- Inspectability over opacity
- Determinism before AI judgment
- Local control over remote dependence
- Replaceable adapters over provider lock-in
- Vertical slices over speculative platform-building
