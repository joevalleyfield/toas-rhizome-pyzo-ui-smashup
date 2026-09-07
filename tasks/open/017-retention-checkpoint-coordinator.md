# 017: Automatic checkpoint scheduling and durability barrier

## Status

WAITING — owner unclaimed; intended executor Luna.
Dependencies: 016 completed with evidence and committed.

This is a bounded Experiment 014 follow-up, not a new product phase. Read and
follow [the batch execution contract](../local-retention-batch.md), which defines
scope, isolation, commit authority, and completion evidence for every task.

## Outcome

Implement a testable retention coordinator around immutable snapshots and the existing persistence store, without live Qt wiring.

## Read before editing

Under `spikes/peer_frames/` unless a different path is specified: `workspace_persistence.py`, `application_lifecycle.py`, `session_recovery.py`, and their failure/rollback tests.
Also read the normative [September amendment](../../docs/local-workspace-scope-2026-09-06.md)
and predecessor completion evidence.

## Allowed writes

New `spikes/peer_frames/retention.py` and `test_retention.py`; minimal persistence API additions and matching tests only if required.
This task's status/evidence and `docs/evidence/task-017-local-retention.md`
are also allowed. Other writes require a bounded handback, not inferred scope.

## Decisions and boundaries

- Inject clock, scheduling, capture, and writer interfaces so tests use fake time rather than sleeps.
- Engineering starting point: a checkpoint becomes due no later than one second after the first unpersisted edit; sustained typing must not postpone it indefinitely. Completion latency is separately measured and reported.
- Capture consistent immutable state on the owning thread. Allow one writer at a time; coalesce pending snapshots to the latest revision without letting older completion clear newer dirty state.
- Expose pending, durable, and failed states and a flush barrier for close/restart. Return explicit failure; never claim durability based on scheduling alone.
- Do not write source files or silently purge retained history.

## Acceptance

- Continuous edits hit the due deadline; idle time creates no redundant writes.
- Edits during a write remain pending until their own generation completes.
- Write failure retains pending state, reports failure, and supports retry.
- Flush with unchanged state succeeds; flush with pending state waits for the required revision or fails visibly.
- A stale completion cannot publish itself as newer durable state.

## Stop boundary

If the existing writer cannot support ordered publication without redesign, record the boundary and return for review.
Use REVIEW_REQUIRED or BLOCKED with the smallest reproduction and a concrete
question. Do not mark partial implementation complete or enable dependent work.

## Completion evidence

Pending. Record changed behavior, meaningful before/after assertions, commands,
results, remaining limits, and separate root/Pyzo revisions under the batch
contract. Move to COMPLETE only when all acceptance criteria are satisfied.

