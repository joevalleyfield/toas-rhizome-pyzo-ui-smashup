# 019: Wire the approved retained-document editor adapter

## Status

COMPLETE — owner Codex; completed 2026-09-13.
Starting root revision: `4786d2ca`; starting Pyzo revision: `e46e1cf8`.
Dependencies: 018 explicitly reviewed and accepted by Astra; 015–017 complete.

Final Pyzo revision: `bdb55074`; final root evidence revision follows.

Current checkpoint: Pyzo revision `1210fda4` wires the approved adapter into
peer editor lifecycle binding, persistence restore/save, close teardown, and
owner-scoped callback cleanup. Isolated Qt smoke reaches the peer workspace
round-trip, pane movement, clean/dirty editor lifecycle, and zero-frame checks;
focused tests and lint pass. Full 019 acceptance and separate-process
round-trip evidence are complete. Task 020 is now eligible.

This is a bounded Experiment 014 follow-up, not a new product phase. Read and
follow [the batch execution contract](../local-retention-batch.md), which defines
scope, isolation, commit authority, and completion evidence for every task.

## Outcome

Integrate the accepted proof into live peer editors and connect mutations to retention checkpoints.

## Read before editing

Under `spikes/peer_frames/` unless a different path is specified: 018 evidence and approved approach; `deps/pyzo/pyzo/core/applicationController.py`, `editor.py`, and `_bindPeerEditorLifecycle` in `main.py`.
Also read the normative [September amendment](../../docs/local-workspace-scope-2026-09-06.md)
and predecessor completion evidence.

## Allowed writes

`deps/pyzo/pyzo/core/applicationController.py`, `editor.py`, `editorGroups.py`, document registration portions of `main.py`; new focused `core/documentRetention.py` if justified by the accepted proof; matching nested tests.
This task's status/evidence and `docs/evidence/task-019-local-retention.md`
are also allowed. Other writes require a bounded handback, not inferred scope.

## Decisions and boundaries

- Follow the reviewed 018 approach exactly at the ownership boundary; preserve vanilla/legacy behavior through the existing explicit peer-mode boundary.
- Bind every peer editor to one retained document and one view identity. Resolve an already-open file to the existing document, not a duplicate resource.
- Wire text/history/view-state changes into 017. Save updates the clean baseline without clearing retained history. Preserve BOM, encoding, line endings, and parser provenance.
- Checkpoint I/O must not mutate editor widgets from a worker thread; pending/error state is available to application services.
- Keep lifecycle close/reopen UI changes for 020.

## Acceptance

- Repeat 018 cases through the real application adapter, including duplicate file opens and Save followed by Undo.
- Checkpoint and restore real editor text/history/view state in a fresh process with isolated settings.
- Parser stale-result tests and existing editor/application-controller tests pass.
- One document change produces bounded notifications; programmatic projection must not create a second user edit.

## Stop boundary

Any departure from 018's approved undo/history mechanism requires Astra review rather than another unreviewed implementation.
Use REVIEW_REQUIRED or BLOCKED with the smallest reproduction and a concrete
question. Do not mark partial implementation complete or enable dependent work.

## Completion evidence

Pending. Record changed behavior, meaningful before/after assertions, commands,
results, remaining limits, and separate root/Pyzo revisions under the batch
contract. Move to COMPLETE only when all acceptance criteria are satisfied.
