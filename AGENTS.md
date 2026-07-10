# AGENTS.md

## Repository role

This repository contains the AgentFlow product itself: architecture documents, templates, and a thin Python scaffold.

## Current guidance

- Keep orchestration logic separate from presentation surfaces.
- Prefer small, testable vertical slices.
- Do not let adapters own task state transitions.
- Preserve repository-local inspectability for task artifacts.
