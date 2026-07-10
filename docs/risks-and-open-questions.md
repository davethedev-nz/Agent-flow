# Risks And Open Questions

## Major risks

- Provider output may be unstable even with explicit schemas.
- Git and worktree operations can vary across local environments and repo layouts.
- Command policy enforcement can become too strict or too permissive if not carefully modeled.
- Mixed monorepos may strain simple path-based detection and validation defaults.
- Non-progress detection may create false positives or false negatives.
- Repository-local task artifacts may become noisy if raw logs are over-retained.

## Mitigations

- use strict schema validation plus raw-output persistence
- keep adapter contracts narrow and swap-friendly
- prefer subprocess argv execution instead of shell strings
- make path and command policies explicit and inspectable
- start with one worktree and one repair loop path
- define retention and `.gitignore` defaults clearly

## Open questions

- Should large run logs and raw provider transcripts be Git-ignored by default or committed selectively?
- Should the first reviewer adapter be the same provider family as the implementer or intentionally different?
- How much project detection should `agentflow init` automate before it becomes opaque?
- Should SQLite be mandatory from slice 6 onward or optional until cross-project features appear?
- What is the right default granularity for command approval in mixed infrastructure repositories?
- Should checkpoint commits appear before the final-approval slice or remain a later enhancement?

## Assumptions

- the initial product is operated by one developer at a time per task
- local Git is available in target repositories
- external agent providers are invoked through local CLIs or equivalent subprocess-hosted tools
- inspectability matters more than raw automation speed in the MVP
