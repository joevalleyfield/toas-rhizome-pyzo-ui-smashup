# Retention integration review — 2026-10-04

Authority: user's continuation and roadmap-cleanup request. The September
scope amendment remains normative. Reviewed starting root `d50c07af` and Pyzo
`776cf29c`. Initial read-only JJ status did not snapshot the working files;
later normal snapshotting revealed existing September review-document edits,
which were preserved and committed separately at root `b0705f64`.
Pyzo was clean before the new correction. This is a current Codex review,
not a claim that Astra approved historical unrecorded gates.

## Current verdict

018 and 021a are accepted at the current revisions after review and validation.
The 015–022 retained-editor workflow passes. Broader integration remains
REVIEW_REQUIRED until explicit ambiguous legacy recovery selection is supplied
by [024](../../tasks/open/024-legacy-recovery-selection.md). Stage 4 is not
accepted or unlocked by a green 022 harness alone.

## Focus correction and coverage

The full isolated peer smoke reproduced failure at `main.py:4160`: focusing
the first shell left the second shell selected. Peer focus returned after its
editor-host loop, before its legacy shell-host loop. Native widget focus also
scanned only the primary runtime backend. The correction selects shell hosts
within the explicitly owning runtime and scans each runtime for descendant
focus. Unknown docks cannot fall through to compatibility host selection.

The 15-case matrix failed five product cases before the correction (10 passed)
and passes all 15 afterward. It covers both runtime owners, editor/shell/tool
docks, absent/retired focus, duplicate events, owner-switch sequences, legacy
routes, and widget/descendant focus. Execution affinity remains unchanged.
Initial fixture collection/setup errors were corrected before taking these
product measurements; they were not counted as product failures or skips.

Full peer smoke now completes the unchanged movement, editor/shell close,
zero-frame recreation, Run/live debug, postmortem, and multi-kernel assertions.
This identifies a concrete routing defect; it does not claim an exhaustive
root-cause cure for every historically intermittent Qt projection failure.

## Independent validation

```sh
RUN_LOCAL_RETENTION_ACCEPTANCE=1 PYTHONPATH=. ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest pytest spikes/peer_frames/test_local_retention_acceptance.py -q
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest --with PySide6 --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs
```

Before the focus correction: 7 live tests passed in 24.98s; 282 combined tests,
8 skips, 33 subtests passed in 3.65s. After correction: 297 combined tests,
8 skips, 33 subtests passed in 2.32s. Seven skips are opt-in live controls run
separately; one is the stock backend control superseded by the four-side fork.
Two existing Qt high-DPI deprecation warnings remain.

Reproducible isolated full application controls:

```sh
PYTHONPATH=. ./.codex-local/bin/uvt run --offline --python 3.12 python - <<'PY'
from pathlib import Path
import tempfile
from spikes.peer_frames.test_local_retention_acceptance import ROOT, run_owned_probe
for phase in ('peer', 'legacy'):
    with tempfile.TemporaryDirectory(prefix='pyzo-integration-'+phase+'-') as directory:
        elapsed, output = run_owned_probe(phase, Path(directory), probe=ROOT / 'spikes/peer_frames/qt_application_smoke_probe.py', deadline=35)
        assert f'APPLICATION SMOKE {phase} COMPLETE' in output, output
        print(phase, elapsed, output)
PY
```

Peer passed in 11.482s; legacy non-peer passed in 7.354s. Logs:
[peer](runtime-smoke-2026-10-04/peer.log),
[legacy](runtime-smoke-2026-10-04/legacy.log). Test-only paths redirect config,
data, workspace/recovery and logs. The command-server module is stubbed to
avoid the user's listener; kernels are real and belong to the owned process
group. Host assertions verify zero QMainWindow instances in peer mode and the
ordinary QMainWindow in legacy mode. The non-peer fork path is the available
compatibility control; an independent pristine upstream Pyzo or published-wheel
control is not claimed. Native macOS drag/accessibility and Windows/Linux
replay remain later portability obligations.

Accepted focus correction: Pyzo `e7274793`. Binding checkout `b8d9c0a7`
(the prebuilt dev10 wheel is used; no binding changes).

## Migration gate

Storage tests prove divergence and malformed inputs remain backed up, retained,
and reported across restart. Inspection finds no explicit selection operation
for `application_state.legacy_recovery.candidates`. A warning alone cannot
complete the amendment's explicit choice requirement. 024 must preserve all
candidates/provenance, durably select without source writes, block ordinary
editing of unresolved source paths, preserve unrelated documents, and cover
cancel/failed-publication/restart. File Move/Fork UX, full workspace execution,
debugger overlays and contextual tools remain pending after this gate.
