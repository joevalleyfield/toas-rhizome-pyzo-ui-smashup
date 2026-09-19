# Task 021a0 progress evidence: runtime-owned frame chrome

Date: 2026-09-18
Status: COMPLETE

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

The configured real-Qt startup matrix now reaches all functional peer-frame
markers, including pane movement, clean and dirty editor lifecycle, zero-frame
recovery, ordinary run/debug, post-mortem, and multi-kernel affinity. The old
dirty-close assertions were updated to reflect 020: final-view dirty close
retains without Save/Discard, while explicit Save remains separately tested.

## Remaining acceptance work

The delayed Pyzo `showRunCursor` callback was made editor-owned in the first
021a1 correction, so destruction cancels it. The real-Qt matrix then completed
with no callback traceback. Broader external-deadline and test-abort cleanup
remain in 021a1.

## Completion marker

```text
Pyzo real-pane movement matrix smoke test passed
Pyzo clean editor lifecycle matrix smoke test passed
Pyzo dirty editor lifecycle matrix smoke test passed
Pyzo independent shell-dock smoke test passed
Pyzo zero-frame survival and default recreation smoke test passed
Pyzo ordinary run and live-debug smoke passed
Pyzo post-mortem re-entry smoke test passed
Pyzo multi-kernel execution-affinity smoke test passed
no callback traceback
```

## Reproduction environment

Runs use the configured `.codex-local/bin/uvt` launcher, Python 3.12, pinned
PySide6-QtAds, isolated app-data/tools/workspace paths under `/tmp`, and
`PYZO_PEER_FRAMES=1`. No user Pyzo app-data is used.
