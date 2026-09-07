# 015: Retained documents and revised acceptance contract

## Status

READY — owner unclaimed; intended executor Luna.
Dependencies: None. READY; this is the only initially ready task.

This is a bounded Experiment 014 follow-up, not a new product phase. Read and
follow [the batch execution contract](../local-retention-batch.md), which defines
scope, isolation, commit authority, and completion evidence for every task.

## Outcome

Implement the pure-model retained-document boundary and reconcile affected Stage 2–3 criteria before changing behavior.

## Read before editing

Under `spikes/peer_frames/` unless a different path is specified: `document_resources.py`, `lifecycle.py`, `test_document_resources.py`, `test_lifecycle.py`, and Experiment 014's Stage 2–3 sections.
Also read the normative [September amendment](../../docs/local-workspace-scope-2026-09-06.md)
and predecessor completion evidence.

## Allowed writes

`spikes/peer_frames/document_resources.py`, `spikes/peer_frames/lifecycle.py`, their matching tests, and the affected Stage 2–3 acceptance criteria in `tasks/open/014-concurrent-workspace-implementation.md`.
This task's status/evidence and `docs/evidence/task-015-local-retention.md`
are also allowed. Other writes require a bounded handback, not inferred scope.

## Decisions and boundaries

- Keep document identity/text/clean baseline/undo/redo after zero live views. A detached view cannot receive callbacks or authorize operations merely because the document remains retained.
- Preserve a closed-view descriptor for reopening, including workspace/document IDs and view state; distinguish explicit tab closure from workspace suspension.
- Expose retained/closed-buffer enumeration and reopen by identity, including untitled documents. No path-based guessing of a replacement identity.
- Preserve existing explicit Save/Discard behavior as separate operations; add the retention close policy without prematurely switching live Pyzo to it.
- Revise only the current acceptance contract in Experiment 014; date and preserve earlier completion evidence. Mark later migration and Qt requirements as pending, not passed.

## Acceptance

- Edit/undo/redo; close the last view; reopen with the same identity, text, history, and view state.
- Two views share content but retain different cursors; closing either cannot call the document Save/Discard handler.
- Closing a view invalidates its callback token; document-level retention remains accessible.
- Named and untitled closed-buffer enumeration; failed reopen leaves retained state intact.
- Existing rename/branch and explicit-disposition tests still pass or have a cited superseding requirement.

## Stop boundary

Do not implement disk storage, Qt editor wiring, or a new identity system.
Use REVIEW_REQUIRED or BLOCKED with the smallest reproduction and a concrete
question. Do not mark partial implementation complete or enable dependent work.

## Completion evidence

Pending. Record changed behavior, meaningful before/after assertions, commands,
results, remaining limits, and separate root/Pyzo revisions under the batch
contract. Move to COMPLETE only when all acceptance criteria are satisfied.

