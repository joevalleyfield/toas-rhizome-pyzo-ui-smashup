# Retention integration review — 2026-10-04

Authority: user's continuation and roadmap-cleanup request. The September
scope amendment remains normative. Reviewed starting root `d50c07af` and Pyzo
`776cf29c`. Initial read-only JJ status did not snapshot the working files;
later normal snapshotting revealed existing September review-document edits,
which were preserved and committed separately at root `b0705f64`.
Pyzo was clean before the new correction. This is a current Codex review,
not a claim that Astra approved historical unrecorded gates.

## Current verdict

**Accepted: the September retained-document batch, including corrections 024
and 025.** The current 018/021a gates are recorded, explicit legacy choices are
available, and the shared-view/runtime close/restore defects are corrected.
This is a current Codex decision under the user's continuation authority;
Astra's September amendment and dated prior reviews remain intact.

Stage 4 live integration is not accepted by these results. Its first bounded
follow-up is [026: live workspace Execute Selection](../../tasks/open/026-live-workspace-execute-selection.md).
File Move/Fork UX, explicit execution assignments, all Run variants, debugger
isolation, contextual tools and full platform/compatibility acceptance remain
pending. Portable synchronization, live shell migration and zombies are deferred.

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

## Initial review measurements

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

## Explicit migration selection and retained reopening

024 adds a File menu recovery action with version choice, readonly working text
and clean-baseline previews, and Undo/Redo counts. Matching unresolved source
paths (including aliases and malformed-only raw records) cannot acquire an
editable view without explicit selection. A valid existing document authority
cannot be overwritten by archived divergence. Named and untitled choices are
validated, atomically published as retained resources, then adopted into the
live registry without replacing unrelated documents or notification bindings.

All candidates, raw legacy config, provenance and the migration backup remain
preserved. Selection retains baseline/history and text metadata. Closed selected
buffers reopen retained text rather than the source file. Real-app proof checks
cancellation, failed publication/retry, full version preview, BOM/CRLF, Undo/Redo,
healthy editor continuity, selection into a secondary runtime, native editor
close, restart and unchanged named/malformed source bytes. Six store/registry
controls cover malformed history, invalid choice/owner, existing authority/path
collision and failed atomic publication.

Cancellation performs no write. The live operation first flushes unrelated
pending edits; therefore an injected selection failure can still follow a valid
ordinary checkpoint. The selection transaction itself preserves its input
generation on publication failure. This distinction is asserted at the store
boundary and documented here rather than claiming every live failure prevents
an unrelated retention generation.

## Shared-view and runtime corrections

Expanded replay after focus routing reproduced retired `view-a` remaining in
the editor manager, stale native editor access, failed saved-primary B startup,
and lost shared text after processing Qt callbacks. The close registry detached
only the final view using the first registered lifecycle. It now detaches each
closed view through its own lifecycle and transfers final-close authority to a
remaining live view. The document adapter rejects queued callbacks from unbound
editors before reading retired state or mutating the shared resource.

Startup chooses a usable requested owner, records failures for retry and keeps
failed requested identities in subsequent manifests. Native restore/teardown
focus cannot select service hosts, and refused activation cannot select a host.
Modern retained state suppresses legacy path replay; old disk text and duplicate
views can no longer be admitted through that second startup path. Native editor,
pane and frame closure resolve the addressed runtime rather than primary aliases.
Zero-frame behavior considers all runtimes.

The all-requested-owner extension independently reproduced invalid bootstrap
active/recovery fields during checkpoint. Publication now preserves the requested
A/B loaded set and exact prior workspace/document records; temporary bootstrap
views/recovery do not enter those records. Both failed requests can then retry.
Suspended known C recovery remains valid and preserved. An initial assertion
incorrectly excluded known suspended recovery; it was corrected against the
store's known-workspace schema, while preserving the no-bootstrap assertion.
The added test-only import shadow was corrected before final acceptance.

Meaningful before/after counts are in [025](../../tasks/open/025-shared-view-close-and-restore.md).
Initial fixture collection failures are not product evidence. The full peer
smoke retains its existing assertions; no timeout increase or retry wrapper
turns an application failure into a pass. The reproduced focus/lifecycle/startup
causes are corrected; this is not an exhaustive claim that every historical
intermittent Qt issue shared those causes.

## Final validation and limits

Final commands are the combined and live commands above, with the full smoke
runner unchanged. The live matrix now includes nine test-owned process controls.
Runtime: Python 3.12.13, PySide6/Qt 6.11.1, local QtAds dev10 wheel. Binding checkout
remains `b8d9c0a7`; no QtADS/binding or TOAS/Rhizome changes.

Source compilation and root/nested added-line whitespace checks pass. Touched
files pass Ruff name/import diagnostics after bounded cleanup. Full repository
lint is not claimed; a pre-existing `zip` strictness warning remains in the
runtime test outside the new case. Nine opt-in live tests run separately; the
remaining default skip is the stock tab-side control superseded by the fork.
Two existing high-DPI deprecation warnings remain.

Native macOS window-manager drag/accessibility and Windows/Linux evidence are
still portability obligations. Legacy non-peer mode uses the maintained local
fork, not an independent pristine upstream/published wheel. Sustained checkpoint
latency/history/storage controls retain their bounded assertion thresholds;
unbounded production soak or storage-compaction acceptance is not implied.
Cross-workspace shell transfer refusal and complete live execution ownership
are Stage 4 obligations, not claimed by this retention acceptance.

## Accepted revision ledger

Final combined result: **326 passed, 10 skipped, 45 subtests**, 2.25s. Final
live result: **9 passed**, 27.01s. Full peer smoke: **11.362s**; full legacy
non-peer smoke: **7.481s**. Logs are retained in the linked runtime-smoke directory.
The combined/live output summaries are also saved there for reproducibility.
The Pyzo changes for 024/025 share the same startup/close source boundary and are
committed together as one bounded retention integration correction; the root
lifecycle and selection publications have separate commit boundaries.

| Boundary | Accepted commit |
| --- | --- |
| Existing September 022 review documents preserved | root `b0705f64d1d532a30c983027c5ec3d6c1aedfb0c` |
| Initial gate/focus reconciliation | root `0586f141`, Pyzo `e7274793` |
| Shared-view lifecycle | root `0448eee85ba2ce8a12ca4d3a04b3853b4debd961` |
| Explicit selection and final live probes | root `7b9bed427aed0129a83a14acb96a8fc50db024a7` |
| Pyzo selection/runtime integration | Pyzo `ed7cfb868b899b9680ad8ee127dd11dd7f57248d` |

Root `7b9bed42` requires Pyzo `ed7cfb86` for the new live controls. The final
roadmap/evidence cleanup is the subsequent coordinating commit; it changes
no production code and leaves exactly one NEXT item, 026. Both working copies
are verified clean after the accepted commits. Nothing was pushed.
