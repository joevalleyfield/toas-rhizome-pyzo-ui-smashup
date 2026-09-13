# 020: Retain closed buffers and expose reopen UI

## Status

IN_PROGRESS — owner Codex; started 2026-09-13.
Starting root revision: `3d32a11b`; starting Pyzo revision: `bdb55074`.
Dependencies: 019 complete and committed.

This is a bounded Experiment 014 follow-up, not a new product phase. Read and
follow [the batch execution contract](../local-retention-batch.md), which defines
scope, isolation, commit authority, and completion evidence for every task.

## Outcome

Make ordinary peer document closure retain state, and provide a usable closed-buffer list.

## Read before editing

Under `spikes/peer_frames/` unless a different path is specified: `lifecycle.py`, `_requestPeerEditorClose`, `_resolvePeerEditorClose`, `_closeCommittedPeerEditor`, `_retirePeerRecoveryForEditor` in Pyzo `main.py`, and `editorTabs.py`/`menu.py` close and Save paths.
Also read the normative [September amendment](../../docs/local-workspace-scope-2026-09-06.md)
and predecessor completion evidence.

## Allowed writes

`spikes/peer_frames/lifecycle.py`, matching tests; Pyzo `main.py`, `editorTabs.py`, `menu.py`, `applicationController.py`, and focused tests for these paths.
This task's status/evidence and `docs/evidence/task-020-local-retention.md`
are also allowed. Other writes require a bounded handback, not inferred scope.

## Decisions and boundaries

- Final-view close uses the durability barrier and detaches only after successful retention. It never triggers Save/Discard merely because it is the final view.
- Retention failure offers Retry or Cancel Close while preserving the buffer. Existing explicit Save and Discard remain separately available.
- Add a minimal Retained Buffers list showing display name/path, dirty marker, and remembered workspace. Reopen selected buffers by identity into an explicit destination workspace.
- List ambiguous legacy migration candidates from 016 through explicit review/selection; preserve unselected versions. No silent overwrite or background resolution.
- Closing a tab remains closed after restart; reopening a workspace restores only its remembered open-view arrangement.
- Keep pin protection and shell-close semantics intact. Do not add automatic retention purging.

## Acceptance

- Named and untitled final-view closure, reopen, restart, Save, and explicit Discard.
- One of two views closes with no disposition; remaining view and undo state stay intact.
- Retention error cancels teardown; retry succeeds without duplicate close callbacks.
- Closed buffers are discoverable with zero open views; selection cannot attach a different document by a reused filename.
- Update old clean/dirty smoke assertions only where the amendment explicitly changes their expected behavior.

## Stop boundary

Do not broaden into a document browser redesign or erase old recovery records merely to make the list simpler.
Use REVIEW_REQUIRED or BLOCKED with the smallest reproduction and a concrete
question. Do not mark partial implementation complete or enable dependent work.

## Completion evidence

Pending. Record changed behavior, meaningful before/after assertions, commands,
results, remaining limits, and separate root/Pyzo revisions under the batch
contract. Move to COMPLETE only when all acceptance criteria are satisfied.
