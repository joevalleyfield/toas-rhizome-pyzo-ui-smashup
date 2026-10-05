# Workspace Run variants — accepted 2026-10-05

[Task 028](../../tasks/open/028-live-workspace-run-variants.md) closes the existing
remaining editor Run routes gate in [014 Stage 4](../../tasks/open/014-concurrent-workspace-implementation.md#4-workspace-execution-routing-and-shell-transfer-refusal).
The [September amendment](../local-workspace-scope-2026-09-06.md) remains normative.
Full Stage 4 is still pending native request/result provenance.

Accepted root implementation: `7859b4fa2f388c49d0801c53b53aa48ec4a19273`.
Accepted Pyzo implementation: `43a1376ecf3a4447ce93ef78cee5e77bf2e771d5`.
Starting root/Pyzo: `a4ff0bf5` / `19d619a0`. The binding working copy remains at
its pre-existing `b8d9c0a784db678227833ef8e545765a974ad4cb`; its packaging changes
were untouched. The pinned wheel remains
`pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl`.
The coordinated/QtADS and live application graphs use Python **3.12.13**,
PySide6/Qt **6.11.1**. A separate PySide-only compilation graph uses 6.11.2;
the final compilation/whitespace check also passes in the coordinated graph.

## Result

Cell/Cell-and-Advance, Execute File/Main and both Run-as-Script variants now use
the invoking native view's workspace/assignment resolver. File context actions
use their addressed editor, independent of global current editor/Run target.
Implicit routing retains the no-fallback rule; explicit/broken assignment and
native lifetime/generation guards from 026/027 apply to every variant. Advance
uses the captured editor and occurs only after successful dispatch.

Execute preserves buffer content, line/cell metadata, directory configuration
and run highlight without saving. Main uses the invoking workspace's retained
document reference, rather than a global open-editor scan. Execute Main works
without opening a view. Native designation saves pathless documents first,
checks the captured view after modal save, and projects workspace-local markers.
Binding/reopening cannot replay a stale main designation; a legacy main flag is
consumed only during initial document migration.

Script resolves its target before autosave and revalidates the invoking/source
views, main reference, target and generation afterwards. Cancellation, dirty
save result and stale intent cannot send/restart. Same-document Save As uses the
final saved path. A closed Main may reopen a native view to use the existing
saver. Its BOM, line endings and last clean disk bytes survive retention and
restore. Native external-change cancellation now returns failure before adopting
a false clean baseline. Saved baseline metadata cannot be overwritten by a stale
view and is removed when its document is explicitly forgotten.

Regular Python saves and restarts the captured shell; successful startup has
the same shell identity and a new interpreter generation. Existing IPython
behavior is preserved: `%cd` followed by `%run -i`, with no restart. Live script
provenance records that exception as `recycle=False`; its namespace and generation
remain intact. Run > Execution target now describes all editor execution routes.
The compatibility shell target is labeled Debugger target in peer mode; its
behavior and legacy Run/Debug label remain unchanged.

## Assertions and actual kernels

The new pre-edit resolver assertions initially failed **13/13**, while the prior
36 bridge controls passed: the generalized route and retained Main API were
absent. Focused checks now cover exact cell/File/Main payloads, implicit/explicit
routing, untitled buffers, canceled/dirty saves, Save As, focus drift, retired
Qt views, owner/target/generation/main/source changes and native file-format
snapshot/forget behavior. Existing assignment/router controls remain green.

The [test-owned Qt probe](../../spikes/peer_frames/qt_workspace_run_variants_probe.py)
uses two actual workspace-owned interpreters. It proves cell value 101 with the
next cell unexecuted, independent File values 102/202 and retained Main values
301/401. All Execute source bytes remain unchanged. It independently designates
A/B mains through the native context menu, executes a closed Main without opening
it, persists both identities, and refuses an unavailable main without fallback.
Native binding cannot reassert a cached designation.

Real File as Script saves B and recycles B while A's context/namespace remain.
Main as Script reopens the retained A source, preserves UTF-8 BOM/CRLF, saves its
explicitly relocated path and recycles A. Fresh receipts prove new generations;
old receipts/results are rejected. An actual external-change save prompt is
canceled in the test, leaving file bytes and retained baseline intact with no
restart. A real IPython B kernel then executes both script variants, preserving
its generation and producing namespace values 503/504 from a retained value 502.

The cell harness explicitly refreshes native highlighting, which is lazy for a
hidden editor. Test-owned shutdown supplies terminate decisions for its kernels;
this is teardown, not new workspace-close policy. Failed harness attempts were
deadline bounded and cleaned; the final replay completes normally.

## Validation and cleanup

| Check | Result |
| --- | --- |
| Coordinated root/Pyzo suite | **420 passed, 13 skipped, 45 subtests**, 2.36s |
| Opt-in retention/execution controls | **12 passed**, 40.67s |
| New real Run variants probe | 5.742s |
| Prior assignment / Selection probes | 4.063s / 3.760s |
| Full peer application Run/debug/postmortem/multiple kernels | Passed, 11.105s |
| Full legacy application control | Passed, 7.309s |
| 13 touched Python sources | Compile; Ruff name/import checks; added-line whitespace pass |

Twelve default skips are the live controls run separately; the remaining stock
four-tab-edge skip and two existing Qt high-DPI deprecation warnings remain.
Logs: [coordinated](workspace-run-variants-2026-10-05/coordinated.log),
[live](workspace-run-variants-2026-10-05/live.log),
[peer](workspace-run-variants-2026-10-05/peer.log),
[legacy](workspace-run-variants-2026-10-05/legacy.log).

Reproduction from the coordinating root:

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest --with PySide6 \
  --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl \
  --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs
RUN_LOCAL_RETENTION_ACCEPTANCE=1 RUN_LOCAL_EXECUTION_ACCEPTANCE=1 PYTHONPATH=. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest python -m pytest \
  spikes/peer_frames/test_local_retention_acceptance.py \
  spikes/peer_frames/test_local_execution_acceptance.py -q -s
```

Full application controls use `run_owned_probe` from the retention harness with
`qt_application_smoke_probe.py`, phases `peer` and `legacy`, fresh temporary
application data and 35-second deadlines. All probes stub the user command server,
run separate owned processes and remove their temporary data. No user source file
was saved, no live user kernel was terminated and nothing was pushed.

Native completion/help/tool/Run/debugger request/result propagation is the next
existing Stage 4 gate. Debugger ownership, breakpoint overlays and conservative
workspace closure remain Stage 5; tools remain Stage 6. Physical macOS interaction
and Windows/Linux native portability are unaccepted by these offscreen proofs.
Live shell migration, zombies, portable synchronization and broad TOAS/Rhizome
integration remain deferred. File Move/Fork UX remains a separate local slice.
