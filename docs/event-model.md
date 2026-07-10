# Event Model

## Role of events

Events are the immutable audit trail and the primary recovery aid. Snapshot state remains the fastest way to answer current-state queries, but snapshots must be reconcilable from the event stream.

## Event format

Each event includes:

- `event_id`
- `task_id`
- `event_type`
- `timestamp`
- `actor`
- `previous_state`
- `resulting_state`
- `correlation_id`
- `causation_id`
- `payload`
- `related_run_id`
- `schema_version`

## Event storage

- append-only `events.jsonl` per task for local portability
- indexed summary in SQLite for cross-project inspection

## Example event types

- task created
- task state changed
- plan requested
- plan generated
- plan approved
- plan rejected
- worktree created
- agent started
- agent completed
- agent failed
- command requested
- command approved
- command rejected
- command executed
- file-scope violation detected
- validation started
- validator completed
- review completed
- finding created
- finding resolved
- repair iteration started
- task blocked
- task resumed
- final approval granted
- commit created
- task completed

## Example record

```json
{
  "event_id": "evt_20260710_0001",
  "task_id": "TASK-001",
  "event_type": "task_state_changed",
  "timestamp": "2026-07-10T15:00:00Z",
  "actor": "agentflow",
  "previous_state": "plan_review",
  "resulting_state": "implementing",
  "correlation_id": "corr_plan_approval_01",
  "causation_id": "approval_plan_01",
  "payload": {
    "approved_by": "developer",
    "approved_plan_hash": "sha256:abc123"
  },
  "related_run_id": null,
  "schema_version": 1
}
```

## Event versus snapshot

- snapshot answers current state quickly
- events explain why the snapshot exists
- reconciliation verifies snapshot correctness

## Idempotency

Commands that can be retried must use stable correlation IDs so a duplicate request does not append duplicate semantically identical events.

## Findings and events

Finding lifecycle changes are also events. Stable finding IDs must survive review iterations so the system can measure progress instead of treating each review as unrelated output.
