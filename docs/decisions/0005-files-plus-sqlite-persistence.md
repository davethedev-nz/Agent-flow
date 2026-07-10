# ADR 0005: Files Plus SQLite Persistence

## Status

Accepted

## Context

Task records should be portable and human-readable, but cross-project queries and indexes are still useful.

## Decision

Use repository-local files for canonical task artifacts and a user-level SQLite database for indexes and metadata.

## Consequences

- Human-readable task history
- Efficient future querying
- Requires reconciliation logic between snapshots, event logs, and indexes
