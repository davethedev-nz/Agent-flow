# Context Construction

## Goal

AgentFlow decides what each agent sees. Agents should not need, or be encouraged, to crawl the entire repository.

## MVP approach

Use deterministic context selection only. No embeddings, vector stores, or semantic indexing.

## Context inputs

Possible sources:

- task requirements
- acceptance criteria
- approved plan
- `.agentflow/project-context.md`
- `.agentflow/architecture-rules.md`
- `AGENTS.md` when present
- explicit files named by the plan
- related tests
- current Git diff
- unresolved findings
- validation results
- recent task events
- repository manifests such as `pyproject.toml`, `package.json`, `.csproj`, `terraform` roots

## Selection strategy by role

### Planner

Include:

- requirements and acceptance criteria
- project context and architecture rules
- relevant manifests
- top-level tree summary
- explicitly requested feature files if named
- nearby tests when easy to identify

### Implementer

Include:

- approved plan or relevant plan sections
- relevant source files
- relevant tests
- unresolved findings for repair iterations
- path and command policy summary
- current diff summary

### Reviewer

Include:

- approved plan
- acceptance criteria
- diff or changed files snapshot
- validation evidence
- unresolved findings history
- architecture rules

### Documenter

Include:

- final diff
- validation evidence
- user-visible behavior changes
- docs path policy

## Deterministic selectors

- explicit path lists from the plan
- configured source and test roots
- `ripgrep` for symbol names or filenames already named in task materials
- neighboring tests by directory convention
- manifests and dependency files at repository root
- current changed paths from Git status or diff

## Transparency requirements

For every agent run, persist a `context/manifest.json` and copies or references to the selected files.

Example manifest:

```json
{
  "task_id": "TASK-001",
  "role": "implementer",
  "files": [
    "src/app/service.py",
    "tests/test_service.py",
    ".agentflow/architecture-rules.md",
    ".agentflow/tasks/TASK-001/plan.md"
  ],
  "selection_reasons": {
    "src/app/service.py": "named in approved plan",
    "tests/test_service.py": "neighboring test under configured test root"
  }
}
```

## Guardrails

- never include forbidden paths
- redact or skip likely secret files where practical
- keep size limits explicit
- use stable ordering for reproducibility
- store the exact prompt and context manifest for post-run inspection

## Future expansion

Later versions may add richer indexing, but the selection algorithm must remain inspectable and overridable by the developer.
