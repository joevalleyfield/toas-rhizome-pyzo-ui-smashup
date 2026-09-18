# Task 021a0 progress evidence: runtime-owned frame chrome

Date: 2026-09-18
Status: IN_PROGRESS

## Implemented

The status and command projectors now accept an explicit owning-runtime frame
provider and expose idempotent `reconcile()` operations. The backend publishes a
settled callback after committed layout synchronization, refreshes its valid
native frame map before publishing, and clears projection activation before
observers run. Removed status bars and per-frame menu bars remove event filters,
hide, and defer deletion. Focus changes to a different pane are no longer
discarded as stale restoration focus.

## Passing checks

```text
PYTHONPATH=. ./.codex-local/bin/uvt run --offline --python 3.12 \
  --with PySide6 --with <pinned QtAds wheel> --with pytest \
  pytest spikes/peer_frames/test_status.py \
  spikes/peer_frames/test_qtads_commands.py -q
18 passed, 3 subtests passed
```

The nested Pyzo runtime/controller/view/shell suite remains green:

```text
6 passed
```

## Remaining acceptance work

The isolated real-Qt startup matrix reaches the pane-movement and clean-editor
lifecycle checks, but does not yet complete deterministically. Recent runs have
alternated between the existing editor-list identity assertion during pane
movement and the projected/live frame equality assertion during cleanup. No
callback traceback from the new projector cleanup path was observed before
those assertions. The next correction must preserve these assertions and
finish the real-Qt matrix; 021a0 remains IN_PROGRESS.

## Reproduction environment

Runs use the configured `.codex-local/bin/uvt` launcher, Python 3.12, pinned
PySide6-QtAds, isolated app-data/tools/workspace paths under `/tmp`, and
`PYZO_PEER_FRAMES=1`. No user Pyzo app-data is used.
