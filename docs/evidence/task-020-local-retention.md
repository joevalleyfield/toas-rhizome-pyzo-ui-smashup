# Task 020 completion evidence: retained closed buffers

Date: 2026-09-18

Task 020 closes the retained-buffer lifecycle that was left pending after 019.
The implementation is split across these committed revisions:

- Root: `4ed8b1b3` (`Cover final retention with multiple live views`), with the
  retained close/reopen probes and the two-view lifecycle coverage.
- Pyzo: `34b10468` (`Persist retained views across workspace saves`), with the
  application/controller wiring, identity-based reopen, and restart merge fix.

## Acceptance results

The focused root suite passed:

```text
PYTHONPATH=. ./.codex-local/bin/uvt run --python 3.12 --with pytest \
  pytest spikes/peer_frames/test_lifecycle.py \
  spikes/peer_frames/test_workspace_persistence.py \
  spikes/peer_frames/test_document_resources.py \
  spikes/peer_frames/test_retention.py -q
84 passed, 17 subtests passed
```

This includes named and untitled retention, non-final/final two-view close,
retention cancellation and retry, explicit discard, identity protection, and
ambiguous/malformed legacy recovery visibility. A retained final close uses the
durability barrier and does not invoke the ordinary Save/Discard negotiation.

The focused Pyzo controller/view/shell suite passed with the pinned QtAds
wheel:

```text
PYTHONPATH=deps/pyzo ../../.codex-local/bin/uvt run --offline --python 3.12 \
  --with PySide6 \
  --with deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl \
  --with ipython pytest tests/test_application_controller.py \
  tests/test_peer_views.py tests/test_shell_groups.py -q
4 passed
```

The real-Qt retained-buffer probe completed its identity-based close/reopen
checks for both named and untitled documents and printed `SECOND`. The fresh
two-process restart probe completed both phases with matching identities:

```text
FIRST 45dfc876a7fa47d3906fa3bcd04a6c11 f52e1d464bc44660a21e97bb95c877f8
SECOND 45dfc876a7fa47d3906fa3bcd04a6c11 f52e1d464bc44660a21e97bb95c877f8
```

The second process verified retained text, dirty state, zero live editors
before reopen, choice-list identity, and identity-based recreation. The
launcher can leave Qt-owned processes alive during shutdown; test-owned
processes were interrupted after their completion markers. That cleanup
limitation is not an acceptance failure, but the harness should eventually
terminate its own shells instead of relying on an interrupt.

## Boundaries

020 proves retention and explicit reopen within the existing attached
workspace. Concurrent live workspace runtimes and durable restoration of a
workspace set remain the 021a/021b/021c prerequisite slices. Closed-buffer
browser redesign, automatic purging, and 020 UI expansion remain out of scope.

Manual OS-level interaction was not used as acceptance evidence; macOS
permissions are available for a supplemental smoke test only.
