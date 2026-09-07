# Task 015 local retention evidence

Date: 2026-09-06

## Delivered boundary

`DocumentResourceRegistry` now keeps a closed-view descriptor after view
closure. The descriptor contains the durable view/document/workspace
identities, copied view state, and an invalidated epoch. The document resource
and its text, clean baseline, undo/redo history, and identity remain available
when its live-view count reaches zero.

Descriptors are enumerable by document identity and reopen by identity,
including pathless documents. Reopen consumes the descriptor only after the
open succeeds and restores it on failure. Snapshot and persistence round trips
include retained descriptors. Forgetting a document referenced by a retained
descriptor is refused.

`DocumentViewRegistry.register_view(..., retain_on_final_close=True)` provides
the model-only retention policy. It records a retained lifecycle descriptor,
invalidates the closed view epoch, and does not call the existing lifecycle
release method. The default remains unchanged, preserving explicit
Save/Discard/Clean disposition behavior for current live integrations.

## State assertions

- Close/reopen preserves document identity, text, undo depth, workspace, and
  view state.
- A closed view token is rejected while the retained document remains present.
- Named and untitled retained views are independently enumerable.
- Reopen with the wrong document identity raises and leaves the full snapshot
  unchanged.
- Opt-in final-view retention records epoch 2 and makes zero lifecycle-release
  calls.

## Verification

Focused suites: 59 tests, OK.

`QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo:. deps/pyzo/.venv/bin/python
-m unittest discover -s spikes/peer_frames -p 'test_*.py'`: 224 tests, OK,
  skipped=1.

The same discovery without `QT_QPA_PLATFORM=offscreen` exits 134 because the
environment has no display (`Cannot create window: no screens available`).

## Scope and handback

Changed only the allowed root model, matching tests, Experiment 014's affected
Stage 2–3 contract notes, and this evidence. No disk storage, Qt editor wiring,
identity-system replacement, Pyzo source, or dependent task was changed.

Next eligible task: 016, versioned retained-state storage and conservative
migration.
