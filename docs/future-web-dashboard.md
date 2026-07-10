# Future Web Dashboard

## Goal

Provide a local HTML control surface without changing the orchestration core.

## Proposed stack

- FastAPI
- Jinja
- HTMX
- SQLite
- server-sent events or polling

## UI views

- project overview
- task overview
- workflow state
- plan and acceptance-criteria matrix
- agent activity
- diff summary
- validation results
- reviewer findings
- event timeline
- context packs
- approval requests

## Architectural rule

The dashboard must render from the same canonical Markdown, JSON, and SQLite-backed query models already used by the CLI. It should not introduce a second state model.

## Future service endpoints

- `/projects`
- `/projects/{project_id}`
- `/tasks/{task_id}`
- `/tasks/{task_id}/events`
- `/tasks/{task_id}/findings`
- `/tasks/{task_id}/validation`
- `/tasks/{task_id}/approvals`

## Deployment stance

Local-only by default. No multi-user session model in MVP.
