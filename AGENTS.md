# AGENTS.md

## Repository role

This repository contains the AgentFlow product itself: architecture documents, templates, and a thin Python scaffold.

## Current guidance

- Keep orchestration logic separate from presentation surfaces.
- Prefer small, testable vertical slices.
- Prefer the least-token approach that still preserves correctness and inspectability.
- Treat delivery estimates as AI-assisted timelines: AI handles most implementation while humans focus on orchestration and review.
- Do not let adapters own task state transitions.
- Preserve repository-local inspectability for task artifacts.
- Implement features on feature branches and merge them through pull requests rather than committing feature work directly to main.
