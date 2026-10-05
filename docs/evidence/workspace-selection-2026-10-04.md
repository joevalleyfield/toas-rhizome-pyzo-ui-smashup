# Workspace Execute Selection — 2026-10-04

Task [026](../../tasks/open/026-live-workspace-execute-selection.md), authorized
by “Take the next item,” is accepted as a bounded live Experiment 014 Stage 4
slice. Astra's September amendment remains normative. This is current Codex
acceptance of 026, not full Stage 4 or retrospective Astra approval.

## Accepted implementation

| Boundary | Revision |
| --- | --- |
| Starting root | `18de8d05dd1de6b346ec49b5f827eb38d002fbab` |
| Starting Pyzo | `ed7cfb868b899b9680ad8ee127dd11dd7f57248d` |
| Root router/probe | `8c458a4fa32eedf2fc6b6d866a265ef02429a590` |
| Pyzo live Selection | `3abb51c5ffaad46d7d6053c9e32bada071eaa664` |
| Binding unchanged | `b8d9c0a7` / local dev10 wheel |

Root `8c458a4f` requires Pyzo `3abb51c5` for the live proof. The coordinating
completion/checklist commit follows these implementations. No TOAS/Rhizome,
QtADS or binding edits, shell migration or zombie behavior. Nothing pushed.

The removed assumption is Selection's application-global shell lookup. Peer
Selection now captures the invoking admitted native view's workspace, resource
view epoch, live shell identity, shell epoch and kernel generation. Dispatch
rechecks those identities and eligibility before invoking the unchanged payload
extraction/send behavior. Selection-and-Advance acts on the captured editor;
print-current-line keeps assignment-result printing and history behavior.

Shell creation, close policy, metadata and explicit closure resolve the owning
native runtime. Normal foreground shell focus updates only that workspace's
Selection target. Starting, unknown, dead or disconnected foreground shells
cannot trigger an older-local or foreign-workspace fallback. Reconnect/restart
advances generation while retaining live shell identity. Confirmed closure
removes the binding and native reference; choosing another target requires an
explicit foreground action. Within-owner movement keeps identity and context.

Legacy non-peer Selection and the File/Main/cell/Run-as-Script compatibility
target remain their existing routes in this slice. Native completion/help/tool/
debugger consumers have not been migrated. The service's tagged result-consumption
seam rejects an actual value captured from the old kernel generation; this is
bounded provenance evidence, not acceptance of every native async callback.

## Reproduced gaps and controls

- Run service regression initially failed (1 failed, 2 passed): selected payload
  went to the global target. Local captured-target, extraction, history, stale
  refusal and captured-editor advance controls now pass.
- Retained view regression initially failed because the router could not register
  the resource epoch. Ten router tests now pass, including an old operation
  rejected after the same view identity reopens at epoch 2.
- Live probe initially failed at `B shell created in primary owner`. After the
  runtime creation correction, two actual namespaces hold values 101 and 202
  despite opposite global-target/focus orders. Only A receives A's multiline code,
  only B receives B's statement, and B has no A-only variable.
- A secondary-owner extension initially failed at `B shell metadata used primary
  model`. Metadata now updates B's model; explicit B closure removes only B's
  shell pane and invalidates B operations while A's shell remains alive.
- A probe status accessor error was corrected to `StatusState.snapshot.message`.
  Initial missing-service test collection is not counted as a product failure.

The live Qt process creates A/B shells, restarts A, and later creates a newer A
shell to disconnect while older A and B remain alive. This proves no local recency
fallback on actual transport loss. A separate shell-free C refuses Selection.
Captured operations cannot send after recycle/loss/view close/shell close; a
prior-generation result is dropped and a current-generation value 42 is accepted.
Native float/redock preserves the shell/context/token. Application/coordinator
transfer refusal leaves both native model layouts unchanged and publishes a
visible status explanation. The saved source bytes remain unchanged by Selection.

Focused controls additionally cover unavailable owners, view transfer, same-ID
view reopen, retired native views, changed focus after capture, replaced context,
starting/dead/disconnected shells, foreign-owner registration and confirmed close
without fallback. The pre-edit coverage matrix is in 026.

## Verification

Runtime: Python 3.12.13, PySide6/Qt 6.11.1, the pinned local
`pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl`.

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest --with PySide6 --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs
RUN_LOCAL_RETENTION_ACCEPTANCE=1 RUN_LOCAL_EXECUTION_ACCEPTANCE=1 PYTHONPATH=. ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest python -m pytest spikes/peer_frames/test_local_retention_acceptance.py spikes/peer_frames/test_local_execution_acceptance.py -q -s
```

Final combined: **344 passed, 11 skipped, 45 subtests**, 2.30s. Ten opt-in live
controls pass separately in 30.60s. Final Selection replay after releasing the
closed-shell foreground reference passes in 3.745s; its 19 focused Run/bridge
controls pass. Ten skipped tests are the opt-in live controls; the other skip is
the stock tab-edge control superseded by the fork. Two existing high-DPI
deprecation warnings remain. Touched Python syntax, Ruff name/import diagnostics
and root/nested added-line whitespace checks pass.

The unchanged full smoke launcher is in the
[retention integration evidence](retention-integration-2026-10-04.md#initial-review-measurements).
Full peer: **11.220s**; legacy non-peer: **7.377s**. It retains Run/live-debug,
postmortem, multi-kernel and lifecycle assertions. These full smokes and the ten
live controls preceded the final reference-only closure cleanup; the final
combined/focused and actual-kernel Selection checks cover that cleanup.
Logs: [combined](workspace-selection-2026-10-04/combined.log),
[live controls](workspace-selection-2026-10-04/live.log),
[final Selection](workspace-selection-2026-10-04/selection.log),
[peer](workspace-selection-2026-10-04/peer.log),
[legacy](workspace-selection-2026-10-04/legacy.log),
[initial ownership failure](workspace-selection-2026-10-04/ownership-before.log),
[secondary metadata failure](workspace-selection-2026-10-04/metadata-before.log).

All subprocesses use fresh test-owned config/data/workspace/recovery paths,
stub the user's command listener and run real kernels. External deadlines kill
only the owned process group on failure. Existing deadlines/assertions were not
relaxed; the new Selection probe has its own 35-second external cap.

## Remaining gates

The checklist returns to the existing Stage 4 explicit-assignment/broken-target
gate, then all remaining Execute/File/Main/Run-as-Script routes and native
request/result provenance. Stage 5 debugger isolation/overlays and Stage 6 tools
remain pending. File Move/Fork UX stays a separate later local slice.

The transfer proof uses the application/coordinator seam and visible native
status bars. It does not claim physical macOS cross-manager drag rejection.
Offscreen float/redock is native QtADS projection, not window-manager drag or
accessibility evidence. Windows/Linux replay and those macOS interactions remain
portability obligations. The legacy control is this maintained local Pyzo fork,
not an independent pristine upstream or published-wheel installation. Live shell
migration, zombies, synchronization and broad TOAS/Rhizome work stay deferred.
