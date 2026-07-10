# MVP Scope

## Included

- installable Python package
- repository initialization for existing Git repositories
- project detection
- project-local configuration
- configuration inheritance with provenance
- task creation and persisted task state
- explicit state transitions
- append-only event logging
- resumability
- one planner adapter
- human plan approval
- one implementation worktree
- one implementer adapter
- command restrictions
- path restrictions
- deterministic validation
- read-only reviewer
- structured findings
- bounded repair loop
- human final approval
- final local commit
- useful VS Code task examples

## Deliberately excluded

- parallel agents
- multiple simultaneous specialist worktrees
- cloud execution
- automatic pushes
- automatic PR creation
- full VS Code extension
- web dashboard
- embeddings and semantic indexing
- distributed queues
- Kubernetes or remote workers
- multi-user access
- billing
- plugin marketplace
- production deployment automation

## Non-goals

The MVP is not intended to be a general autonomous software factory. It is a controlled orchestration tool for a developer operating inside local repositories.
