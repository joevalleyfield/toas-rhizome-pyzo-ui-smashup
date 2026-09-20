# 022: End-to-end retention acceptance and review evidence

## Status

REVIEW_REQUIRED — owner Codex; started 2026-09-20.
Dependencies: 021 complete and committed.

This is a bounded Experiment 014 follow-up, not a new product phase. Read and
follow [the batch execution contract](../local-retention-batch.md), which defines
scope, isolation, commit authority, and completion evidence for every task.

## Outcome

Implement the deterministic integration harness and hand the completed batch back to Astra for acceptance.

## Read before editing

Under `spikes/peer_frames/` unless a different path is specified: 015–021 evidence, amended requirements, existing peer smoke callbacks, `deps/pyzo/pyzolauncher.py`, and `deps/pyzo/tests/check_log.py`.
Also read the normative [September amendment](../../docs/local-workspace-scope-2026-09-06.md)
and predecessor completion evidence.

## Allowed writes

New `spikes/peer_frames/test_local_retention_acceptance.py` and a narrowly scoped isolated launch helper if needed; `deps/pyzo/tests/check_log.py` and test-only smoke helpers in `main.py`/`_start.py` if necessary; evidence documents.
This task's status/evidence and `docs/evidence/task-022-local-retention.md`
are also allowed. Other writes require a bounded handback, not inferred scope.

## Decisions and boundaries

- Launch with a fresh temporary application config/data/workspace/recovery root per test. Redirect the Pyzo path provider before startup if no supported config override exists. Never rely only on workspace/recovery environment variables to isolate user preferences.
- Use the rebuilt interpreter directly; do not let an implicit uv sync remove its Qt dependencies. Use the local binding wheel; source rebuilds are out of scope.
- Inspect callback failures, tracebacks, completion markers, and child-process status; launcher exit code alone is insufficient.
- Include forced-process termination after a durable checkpoint and restart verification. Kill only test-owned PIDs; always clean up test-owned kernels/listeners.
- Reproduce the previously intermittent status-projector mismatch if it occurs; do not weaken assertions, add arbitrary sleeps, or classify one successful run as a fix.
- Report actual checkpoint completion latency during sustained representative edits and retained history size. No production-readiness or Stage 4 completion claim.

## Acceptance

- Exercise the complete revised retention matrix through live editors and separate-process restart, including Undo/Redo and zero-open-workspace recovery.
- Exercise external disk change and failed checkpoint without implicit source writes.
- Run the full coordinating suite and relevant nested tests, plus peer, vanilla, and legacy controls with isolated settings.
- Record exact commands, exit/status checks, logs, runtime versions, root/nested revisions, skips, and unresolved issues.
- Update each task's evidence and populate the self-handoff with completion references for Astra.

## Stop boundary

On product failures, identify the owning task and return for a bounded correction; do not use this harness task to rewrite production lifecycle logic.
Use REVIEW_REQUIRED or BLOCKED with the smallest reproduction and a concrete
question. Do not mark partial implementation complete or enable dependent work.

## Completion evidence

The persistent harness and peer-frame matrix are implemented, but completion
is held by the vanilla-control failure recorded in
`docs/evidence/task-022-local-retention.md`. The normal Pyzo `--test` path
raises before startup completes, even though its launcher returns status 0;
`tests/check_log.py` returns status 1 for the same run. The owning production
correction must land before this task can be marked COMPLETE.
