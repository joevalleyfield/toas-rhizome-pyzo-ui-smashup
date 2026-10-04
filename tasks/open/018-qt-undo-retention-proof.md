# 018: Real-editor undo retention feasibility proof

## Status

COMPLETE — owner Codex; independently reviewed 2026-10-04 under the user's
continuation authorization. All 13 real-editor probe tests pass in the current
combined suite, and the production adapter's shared Undo/Redo and restart
controls pass in the live retention matrix. See
[current integration review](../../docs/evidence/retention-integration-2026-10-04.md).
Dependencies: 017 completed. This closes the missing recorded decision now;
it does not invent a historical Astra acceptance before 019 was implemented.

This is a bounded Experiment 014 follow-up, not a new product phase. Read and
follow [the batch execution contract](../local-retention-batch.md), which defines
scope, isolation, commit authority, and completion evidence for every task.

## Outcome

Build an isolated real-Pyzo-editor proof of shared editing and serializable undo/redo. Establish the adapter approach before production wiring.

## Read before editing

Under `spikes/peer_frames/` unless a different path is specified: `deps/pyzo/pyzo/core/editor.py`, `applicationController.py` document access, `codeeditor/`, `spikes/peer_frames/document_resources.py`, and existing parser/editor tests.
Also read the normative [September amendment](../../docs/local-workspace-scope-2026-09-06.md)
and predecessor completion evidence.

## Allowed writes

New `spikes/peer_frames/qt_document_retention_probe.py`, `test_qt_document_retention_probe.py`, and this task's evidence. No production editor patches.
This task's status/evidence and `docs/evidence/task-018-local-retention.md`
are also allowed. Other writes require a bounded handback, not inferred scope.

## Decisions and boundaries

- Exercise actual Pyzo editor widgets with the local PySide6-QtAds wheel and Python 3.12.
- Prefer the existing application document/history model behind an adapter. Demonstrate how native user edits and undo transactions map to it; do not assume Qt's private undo stack can be serialized.
- Prove keyboard and menu Undo/Redo, paste, selection replacement, deletion, multi-line indent, and an edit after Undo. Cover non-ASCII text and independent selections in two views.
- Serialize, destroy all widgets, then restore fresh widgets and exercise undo/redo. A text-only restore is a failed proof.
- Record editor transaction grouping and notification/reentrancy behavior, with the recommended production approach and its measured limitations.

## Acceptance

- Two live views show the same edits without recursive synchronization and preserve independent selections.
- Undo/redo traverses the same meaningful editing transactions before and after serialization.
- Paste/indent remain coherent user actions; redo is invalidated by a new edit.
- Recreated views restore their state and parser notifications use current identity/revision.
- No source file writes occur during the proof.

## Stop boundary

If this requires replacing Pyzo's editing engine, Qt private APIs, or loses normal undo grouping, mark REVIEW_REQUIRED with evidence. Do not proceed to 019 or reduce undo retention to text recovery.
Use REVIEW_REQUIRED or BLOCKED with the smallest reproduction and a concrete
question. Do not mark partial implementation complete or enable dependent work.

## Completion evidence

See [Task 018 evidence](../../docs/evidence/task-018-local-retention.md).

Record changed behavior, meaningful before/after assertions, commands,
results, remaining limits, and separate root/Pyzo revisions under the batch
contract. Root revision is recorded in the completion commit; no Pyzo source
files were changed.
