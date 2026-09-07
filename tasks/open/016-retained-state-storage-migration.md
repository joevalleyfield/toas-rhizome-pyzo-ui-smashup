# 016: Versioned retained-state storage and conservative migration

## Status

COMPLETE — owner Codex; completed 2026-09-07.
Dependencies: 015 completed with evidence and committed.

This is a bounded Experiment 014 follow-up, not a new product phase. Read and
follow [the batch execution contract](../local-retention-batch.md), which defines
scope, isolation, commit authority, and completion evidence for every task.

## Outcome

Persist application-owned retained documents and workspace references using the existing atomic generation store.

## Read before editing

Under `spikes/peer_frames/` unless a different path is specified: `workspace_persistence.py`, `workspace_recovery.py`, `session_recovery.py`, their tests, and 015's snapshot contract.
Also read the normative [September amendment](../../docs/local-workspace-scope-2026-09-06.md)
and predecessor completion evidence.

## Allowed writes

`spikes/peer_frames/workspace_persistence.py`, `workspace_recovery.py`, `document_resources.py` serialization methods, and their matching tests.
This task's status/evidence and `docs/evidence/task-016-local-retention.md`
are also allowed. Other writes require a bounded handback, not inferred scope.

## Decisions and boundaries

- Extend the existing versioned/checksummed generation format; do not introduce another database or independent authority for document text.
- Persist retained documents even when no workspace/view is open; preserve known workspaces separately from the loaded set and preserve closed-view descriptors.
- Migrate old workspace recovery records without deleting backups or using mtime as authority. Byte-identical editing records may coalesce; preserve distinct text, clean baselines, or histories as recoverable candidates with provenance.
- An unambiguous valid shared record may remain current while divergent legacy candidates remain recoverable. If authority is ambiguous, return a structured unresolved migration issue and block normal editing of that document until explicit selection; healthy unrelated documents/workspaces remain available.
- Preserve unknown fields and restart idempotence. No garbage collection of old generations or retained documents in this task.

## Acceptance

- Round-trip text, undo/redo, dirty baseline, BOM/encoding/line-ending metadata where supplied, open/closed workspace set, and view descriptors.
- Round-trip zero open workspaces without losing documents.
- Equal legacy candidates coalesce; divergent or malformed candidates remain inspectable/recoverable, never silently selected or discarded.
- Fault injection during publication leaves the previous generation readable; retry and repeated migration are idempotent.
- Source file bytes remain unchanged throughout load, migrate, and commit.

## Stop boundary

A storage-format alternative or ambiguous legacy identity policy requires Astra review; do not silently narrow the preservation contract.
Use REVIEW_REQUIRED or BLOCKED with the smallest reproduction and a concrete
question. Do not mark partial implementation complete or enable dependent work.

## Completion evidence

See [Task 016 evidence](../../docs/evidence/task-016-local-retention.md).

Record changed behavior, meaningful before/after assertions, commands,
results, remaining limits, and separate root/Pyzo revisions under the batch
contract. Root revision is recorded in the completion commit; no nested Pyzo
revision was required.
