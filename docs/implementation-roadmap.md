# Implementation Roadmap

## Delivery approach

Build in vertical slices so each slice produces a developer-visible capability and leaves behind tests, not just abstractions.

## Estimation basis

All delivery estimates and pacing assumptions in this roadmap are based on AI-assisted implementation.

- Estimates assume AI tooling performs most code generation, test iteration, and refactoring.
- Human time is primarily orchestration, design decisions, validation, and review.
- Estimates are not calibrated to fully manual implementation timelines.

## Slice checklist

- preserve local-first workflow control
- keep provider adapters replaceable
- persist evidence before adding UX polish
- add tests with every slice

## Progress status

- Completed on this branch: slices 1 through 18
- Remaining: none

## Slice 1: Installable CLI and repository discovery

- User-visible outcome: `agentflow version`, `agentflow doctor`, and `agentflow project inspect` run from an installed package and can locate a repository root.
- Domain changes: project identity and repository-discovery value objects.
- Application-service changes: repository inspection service.
- CLI changes: version, doctor, and inspect commands.
- Persistence changes: none beyond optional debug output.
- Infrastructure changes: Git-root discovery and filesystem inspection.
- Tests: CLI smoke test, repository-root discovery tests, temp-repo detection tests.
- Acceptance criteria: developer can install package, run commands in a temp Git repo, and see deterministic inspection output.
- Dependencies: package scaffold.
- Estimated complexity: small.
- Key risks: Git detection across nested repositories and non-standard remotes.

## Slice 2: Safe `agentflow init`

- User-visible outcome: initialize `.agentflow` with a preview and no accidental overwrite.
- Domain changes: init proposal model.
- Application-service changes: project detector and init preview builder.
- CLI changes: `agentflow init`, optional profile selection, preview confirmation.
- Persistence changes: config and guidance file creation.
- Infrastructure changes: manifest detection for Python, Django, Node, .NET, Terraform.
- Tests: idempotent init, no-overwrite, generated file snapshot tests.
- Acceptance criteria: init is repeatable and safe.
- Dependencies: slice 1.
- Estimated complexity: medium.
- Key risks: good defaults across mixed repositories.

## Slice 3: Configuration resolution

- User-visible outcome: `agentflow config show --resolved` with origin tracking.
- Domain changes: config schemas and provenance model.
- Application-service changes: resolver and merge policies.
- CLI changes: config display commands.
- Persistence changes: user and project config loading.
- Infrastructure changes: YAML loaders and path normalization.
- Tests: inheritance, merge, and provenance tests.
- Acceptance criteria: every resolved setting shows origin.
- Dependencies: slice 2.
- Estimated complexity: medium.
- Key risks: keeping merge rules understandable.

## Slice 4: Task creation and repository-local files

- User-visible outcome: `agentflow task create TASK-001` creates a persisted task record.
- Domain changes: task aggregate, acceptance criteria schema.
- Application-service changes: task creation service.
- CLI changes: task create, list, show.
- Persistence changes: task directory layout and snapshot file writing.
- Infrastructure changes: atomic file writers.
- Tests: task creation and schema validation tests.
- Acceptance criteria: task artifacts are human-readable and recoverable.
- Dependencies: slice 3.
- Estimated complexity: medium.
- Key risks: balancing readability with future extensibility.

## Slice 5: State machine and transition validation

- User-visible outcome: explicit task states and guarded transition commands.
- Domain changes: transition policy.
- Application-service changes: transition coordinator.
- CLI changes: approve-plan, reject-plan, block, resume, status.
- Persistence changes: state snapshot updates.
- Infrastructure changes: none significant.
- Tests: legal and illegal transition tests.
- Acceptance criteria: invalid transitions are rejected deterministically.
- Dependencies: slice 4.
- Estimated complexity: medium.
- Key risks: transition complexity growth.

## Slice 6: Event log and resumability

- User-visible outcome: `agentflow events TASK-001` and safe recovery after interruption.
- Domain changes: event schema and reconciliation rules.
- Application-service changes: event append and resume service.
- CLI changes: events and resume commands.
- Persistence changes: JSONL event log and optional SQLite index.
- Infrastructure changes: event appender and reader.
- Tests: event consistency and recovery tests.
- Acceptance criteria: interrupted operations can be diagnosed and resumed safely.
- Dependencies: slice 5.
- Estimated complexity: medium.
- Key risks: reconciliation edge cases.

## Slice 7: Provider-neutral agent execution

- User-visible outcome: planner and implementer can be invoked through a common adapter contract.
- Domain changes: agent request/result schemas.
- Application-service changes: agent-run coordinator.
- CLI changes: internal wiring used by later plan/run commands.
- Persistence changes: run metadata and raw output persistence.
- Infrastructure changes: subprocess adapter host and fake adapter.
- Tests: malformed output, timeout, and parsing tests.
- Acceptance criteria: one fake adapter and one real CLI adapter path are supported.
- Dependencies: slice 6.
- Estimated complexity: medium.
- Key risks: provider output variability.

## Slice 8: Planner and plan approval

- User-visible outcome: `agentflow plan TASK-001` and `agentflow approve-plan TASK-001`.
- Domain changes: plan schema and approval model.
- Application-service changes: plan request, persistence, approval transition.
- CLI changes: plan and plan approval commands.
- Persistence changes: plan file and approval record.
- Infrastructure changes: planner adapter binding and context builder v1.
- Tests: plan schema validation and approval flow tests.
- Acceptance criteria: approved plans drive later execution.
- Dependencies: slice 7.
- Estimated complexity: medium.
- Key risks: prompt quality versus deterministic schema requirements.

## Slice 9: Git branch and worktree management

- User-visible outcome: task-specific worktree creation after plan approval.
- Domain changes: worktree metadata.
- Application-service changes: worktree orchestration.
- CLI changes: surfaced through run/status commands.
- Persistence changes: worktree record in task state.
- Infrastructure changes: Git and worktree services.
- Tests: temp-repo worktree lifecycle tests.
- Acceptance criteria: worktree reuse and failure detection work reliably.
- Dependencies: slice 8.
- Estimated complexity: medium.
- Key risks: Git portability and local config quirks.

## Slice 10: Restricted command runner

- User-visible outcome: approved commands run through policy enforcement.
- Domain changes: command policy rules.
- Application-service changes: approval request flow.
- CLI changes: approve-command and reject-command.
- Persistence changes: approval records and command events.
- Infrastructure changes: subprocess runner without shell.
- Tests: shell-injection resistance and blocked-pattern tests.
- Acceptance criteria: disallowed commands cannot run through AgentFlow.
- Dependencies: slice 9.
- Estimated complexity: large.
- Key risks: balancing safety with developer convenience.

## Slice 11: Path-policy enforcement

- User-visible outcome: changed files outside scope are detected automatically.
- Domain changes: path rule evaluator.
- Application-service changes: post-run verification.
- CLI changes: clearer blocked-task diagnostics.
- Persistence changes: policy violation events.
- Infrastructure changes: changed-file collection.
- Tests: allowed and forbidden path scenarios.
- Acceptance criteria: out-of-scope edits block progression.
- Dependencies: slice 9.
- Estimated complexity: medium.
- Key risks: correct path normalization across platforms.

## Slice 12: Deterministic validation pipeline

- User-visible outcome: `agentflow validate TASK-001` produces structured evidence.
- Domain changes: validator definitions and result model.
- Application-service changes: validation coordinator.
- CLI changes: validate command and status output.
- Persistence changes: validation result artifacts and logs.
- Infrastructure changes: parser and runner registry.
- Tests: parser tests and timeout handling.
- Acceptance criteria: validators produce structured persisted results.
- Dependencies: slice 10 and slice 11.
- Estimated complexity: large.
- Key risks: normalizing diverse tool outputs.

## Slice 13: Reviewer and structured findings

- User-visible outcome: `agentflow review TASK-001` yields stable findings and a verdict.
- Domain changes: finding identity and severity model.
- Application-service changes: review coordinator.
- CLI changes: review and findings commands.
- Persistence changes: findings store and resolution tracking.
- Infrastructure changes: reviewer adapter binding.
- Tests: finding identity stability and malformed output tests.
- Acceptance criteria: reviewer findings are stable across iterations.
- Dependencies: slice 12.
- Estimated complexity: medium.
- Key risks: noisy or unstable model outputs.

## Slice 14: Bounded repair loop

- User-visible outcome: `agentflow run TASK-001` can implement, validate, review, and repair up to limits.
- Domain changes: non-progress policy.
- Application-service changes: repair loop coordinator.
- CLI changes: run and repair flows.
- Persistence changes: iteration counters and summaries.
- Infrastructure changes: tighter context-builder slices.
- Tests: non-progress detection and iteration limit tests.
- Acceptance criteria: the loop converges or blocks with a clear reason.
- Dependencies: slice 13.
- Estimated complexity: large.
- Key risks: false positives in non-progress detection.

## Slice 15: Final approval and local commit

- User-visible outcome: `agentflow approve-commit TASK-001` creates the final local commit.
- Domain changes: final approval rules.
- Application-service changes: commit gate service.
- CLI changes: approve-commit.
- Persistence changes: final approval record and completion report.
- Infrastructure changes: safe Git commit service.
- Tests: commit gating and completion tests.
- Acceptance criteria: no final commit without explicit approval.
- Dependencies: slice 14.
- Estimated complexity: medium.
- Key risks: preserving accurate commit evidence.

## Slice 16: VS Code task integration examples

- User-visible outcome: init can optionally add useful `.vscode/tasks.json` examples.
- Domain changes: none significant.
- Application-service changes: template selection.
- CLI changes: init options.
- Persistence changes: optional VS Code task files.
- Infrastructure changes: template rendering.
- Tests: template generation tests.
- Acceptance criteria: generated tasks call stable CLI commands.
- Dependencies: slice 2.
- Estimated complexity: small.
- Key risks: keeping templates generic enough.

## Slice 17: Documentation agent

- User-visible outcome: optional documentation pass after stable behavior.
- Domain changes: doc path policy.
- Application-service changes: documentation run coordinator.
- CLI changes: optional doc command or run flag.
- Persistence changes: documentation run artifacts.
- Infrastructure changes: documenter adapter binding.
- Tests: docs-only path scope tests.
- Acceptance criteria: documentation updates stay within doc paths.
- Dependencies: slice 15.
- Estimated complexity: medium.
- Key risks: documentation drift if behavior is still moving.

## Slice 18: Optional tester-agent workflow

- User-visible outcome: separate tester role can improve coverage within test paths.
- Domain changes: tester role policies.
- Application-service changes: tester orchestration path.
- CLI changes: optional test-agent command.
- Persistence changes: tester run records.
- Infrastructure changes: adapter reuse.
- Tests: role restriction tests.
- Acceptance criteria: tester cannot modify production code.
- Dependencies: slice 14.
- Estimated complexity: medium.
- Key risks: overlap with implementer responsibilities.
