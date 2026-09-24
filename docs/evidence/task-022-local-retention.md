# 022 evidence: end-to-end retention acceptance

Latest independent verdict (2026-09-23, root `ec6fdf0e` / Pyzo `41300856`):
**REVIEW_REQUIRED**. Original/latest observation preservation and live resolution
are accepted, but resolution does not schedule an automatic checkpoint. A live
probe found the durable record still conflicted after 1.8 seconds. See the
[fifth review](local-retention-integration-review.md#independent-fifth-review--2026-09-23)
for evidence and the required crash/restart-after-resolution control.

Date: 2026-09-20
Status: REVIEW_REQUIRED

The vanilla blocker was corrected in Pyzo revision `9404bd21`.

## Harness delivered

`spikes/peer_frames/test_local_retention_acceptance.py` is a persistent,
opt-in acceptance harness. It launches the configured `.codex-local/bin/uvt`
with Python 3.12, PySide6, the local QtAds wheel, and isolated temporary
application/workspace data. Each child runs in its own process group; external
deadline expiry terminates only that group and is a failure. The harness checks
markers, tracebacks, teardown failures, and child exit status.

The default test invocation does not launch Qt. The opt-in invocation is:

```text
RUN_LOCAL_RETENTION_ACCEPTANCE=1 PYTHONPATH=. ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest pytest spikes/peer_frames/test_local_retention_acceptance.py -q
```

It passed one test in 3.65 seconds. The matrix reached:

```text
FIRST WORKSPACES workspace-a workspace-b
RETRY FAILURES {'workspace-b': 'injected workspace-b construction failure'}
RETRY WORKSPACES workspace-a workspace-b
VERIFY WORKSPACES workspace-a workspace-b
CANCEL CLOSE workspace-a workspace-b
```

The preceding clean restart slice also passed `FIRST`, `CLOSE workspace-b`,
`CLOSE`, and `REOPEN workspace-a`. No callback traceback, teardown timeout, or
test-owned process leak was observed.

## Suites

Root coordinating suite, with the pinned Qt dependencies:

```text
246 passed, 15 skipped, 33 subtests passed in 2.39s
```

Nested Pyzo suite, with isolated offscreen Qt and the same local dependencies:

```text
22 passed in 1.78s
```

## Blocking control failure

The vanilla Pyzo smoke command was run from `deps/pyzo` with offscreen Qt,
Python 3.12.13, PySide6 6.11.1, the local QtAds wheel, and IPython. Startup
raises:

```text
AttributeError: 'MainWindow' object has no attribute '_peerWorkspace'
```

The launcher returns status 0 despite the traceback. Pyzo's
`tests/check_log.py` correctly returns status 1 and reports the uncaught
exception. This is a production integration regression in the normal
non-peer startup path, not a harness failure. 022 therefore remains
`REVIEW_REQUIRED`; do not mark it complete or claim the vanilla/legacy
controls until the owning task fixes that startup path and the controls are
rerun.

The smallest reproduction is in `pyzo/core/main.py`:
`MainWindow._createEditorHostForRuntime(runtime=None)` assigns
`self._peerWorkspace` before the legacy branch, although legacy startup has no
peer workspace. The assignment is only needed by the peer branch; the vanilla
control therefore fails before its smoke callback can run. This is a bounded
Pyzo pane-integration correction, not an acceptance-harness workaround.

Exact control commands:

```text
PYTHONPATH=. QT_QPA_PLATFORM=offscreen ./.codex-local/bin/uvt run --offline --python 3.12 --with PySide6 --with <local-QtAds-wheel> --with ipython python pyzolauncher.py --test
../../.codex-local/bin/uvt run --offline --python 3.12 python tests/check_log.py
```

The first command printed the uncaught `_peerWorkspace` traceback and returned
0 before the correction; the second returned 1. After the correction, the
normal `pyzolauncher.py --test` path completed all smoke callbacks and
`tests/check_log.py` returned 0. The corrected run used Python 3.12.13,
PySide6 6.11.1, the local QtAds wheel, and IPython. Harness revision: root
`e71868d5`; corrected Pyzo revision: `9404bd21`.

## Additional controls

The forced-crash control passed with a durable checkpoint followed by a fresh
process restoring retained text and Undo/Redo history:

```text
1 passed, 2 deselected in 3.11s
```

The focused recovery, retention, and lifecycle controls passed:

```text
26 passed in 0.06s
```

The live checkpoint and restart control now passes after Pyzo's shutdown
preflight save was made authoritative over the later generic config cleanup:

```text
3 passed in 9.10s
```

The restored editor is recreated as a live editor, reports the clean baseline,
and completes the retained Undo/Redo and duplicate-file identity checks.

The two remaining live controls also pass:

```text
EXTERNAL DURABLE
EXTERNAL CONFLICT
CHECKPOINT FAILED NO SOURCE WRITE
```

The complete opt-in harness now passes:

```text
5 passed in 15.56s
```

The startup-restoration, forced-crash, retry/cancel, external-disk,
failed-checkpoint, sustained-completion, zero-open-workspace, focused model
controls, and vanilla startup gates are clear. The tightened harness reports
per-revision edit-to-write completion rather than a fixed post-workload timer.
It also requires a write during editing, multiple retained history entries,
and storage measured across the complete workspace tree. A representative run
now reports the corresponding `MAX_LATENCY`, `WRITES_DURING_EDIT`,
`HISTORY_ENTRIES`, and `STORAGE_BYTES` fields.

```text
SUSTAINED CHECKPOINT LATENCY 0.107 HISTORY_ENTRIES 1 STORAGE_BYTES 4864
```

The failed-checkpoint control keeps the production writer failure active
through a close attempt, observes the visible error and surviving editor/
workspace, then retries the same coordinator. The external-change control uses
ordinary automatic retention without seeding legacy recovery. On restart it
preserves retained text, records the current external text and signature on the
shared resource, marks the editor warning, and leaves external bytes unchanged.

The persistent zero-open sequence covers first, close, close-empty, and
reopen-empty in separate processes. The complete tightened harness passes
seven tests; 022 remains `REVIEW_REQUIRED` pending review of this evidence.

## Independent review, 2026-09-20

The subsequent [independent review](local-retention-integration-review.md)
confirms the five tests pass, but supersedes the no-control-gaps claim above.
Actual checkpoint timing under sustained edits, failure visibility and close
ordering, external-conflict assertions, and persistent zero-open restart
coverage remain acceptance gaps. Keep `REVIEW_REQUIRED`.

## Independent second review, 2026-09-21

At root `59f94bf3` / Pyzo `0c5c3f20`, the reviewer independently obtained
7 live passes and 281 combined-suite passes (8 explained skips). Zero-open
coverage and failure/close-refusal/retry are accepted. The external-conflict
control depends on manually seeded compatibility recovery, and the latency/
storage metrics still omit the required measurements. See the
[second review](local-retention-integration-review.md#independent-second-review--2026-09-21)
for the unseeded reproduction and bounded corrections. Keep `REVIEW_REQUIRED`.

## Correction follow-up, 2026-09-21

The bounded corrections for the independent second review are implemented.
The ordinary external-conflict control and the sustained metric control pass
as part of the full live matrix; the combined root/Pyzo run passes 281 tests,
with 8 explained skips and 2 existing Qt deprecation warnings. Keep the task
`REVIEW_REQUIRED` until Astra records acceptance.

## Third-review correction follow-up, 2026-09-22

Conflict text, signature, encoding, and conflict state now persist with the
document resource. External-file inspection is source-encoding aware and
handles valid Latin-1 Python files without a decode traceback. The sustained
metric workload relies on automatic scheduling, includes coalesced edits in
edit-to-write latency, and requires a write while editing continues.

The complete live matrix passed 7 tests; the combined root/Pyzo run passed
281 tests with 8 skips and 2 existing Qt deprecation warnings. The task stays
`REVIEW_REQUIRED` pending independent acceptance.

## Independent third review, 2026-09-22

At root `8da4d712` / Pyzo `a48eca2d`, independent runs pass 7 live tests and
281 combined tests (8 explained skips). Acceptance is withheld: external
conflict fields do not survive persistence or have a shared reconciliation
path; the new UTF-8-only detector raises on a valid Latin-1 source; and forced
flushes bypass automatic retention in the sustained workload. See the
[third review](local-retention-integration-review.md#independent-third-review--2026-09-22)
for reproductions and bounded corrections. Keep `REVIEW_REQUIRED`.

## Independent fourth review, 2026-09-22

At root `b7849976` / Pyzo `86f6c70a`, independent verification passes 7 live
tests and 281 combined tests (8 skips). Encoding and automatic-scheduling
corrections are accepted, including a disabled-scheduler negative control.
One conflict-lifecycle blocker remains: restore overwrites serialized unresolved
external state from the current disk contents and can clear the conflict without
reconciliation. The [fourth review](local-retention-integration-review.md#independent-fourth-review--2026-09-22)
records the focused reproduction and required three-process/shared-resolution
coverage. Keep `REVIEW_REQUIRED`.

## Fourth-review correction follow-up, 2026-09-23

Unresolved external observations now survive later disk changes and restart.
The original observed version and a distinct latest observation are persisted
separately. An explicit document-resource resolution clears the conflict and
projects resolved text to all shared views. The live matrix passed 7 tests; the
combined suite passed 282 tests with 8 skips. The task remains
`REVIEW_REQUIRED` pending Astra's final acceptance.

## Fifth-review correction follow-up, 2026-09-23

Explicit external resolution now schedules automatic retention through the
same coordinator callback as ordinary edits. The acceptance control waits for
durability, crashes before orderly shutdown, and verifies resolved text and
cleared conflict state after restart. The live matrix passed 7 tests; the
combined suite passed 282 tests with 8 skips. Keep `REVIEW_REQUIRED` pending
final acceptance.
