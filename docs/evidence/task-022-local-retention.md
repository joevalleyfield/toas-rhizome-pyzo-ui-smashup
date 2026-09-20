# 022 evidence: end-to-end retention acceptance

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

Known limits not yet accepted: forced-crash checkpoint/restart, external-disk
change, failed-checkpoint/source-write control, and sustained checkpoint
latency/history measurements. The vanilla startup gate is now clear; these
remaining measurements still need dedicated controls before 022 can close.
