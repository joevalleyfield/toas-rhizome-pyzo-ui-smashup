# Stage 5 workspace breakpoint and debugger acceptance — 2026-10-06

Local Experiment 014 Stage 5 is **accepted** through
[task 031](../../tasks/open/031-workspace-debugger-and-breakpoint-ownership.md)
under Astra's [September amendment](../local-workspace-scope-2026-09-06.md).
NEXT is the existing Stage 6 gate. Stage 6 implementation, File Move/Fork UX,
live shell migration, zombies/reconciliation, portable synchronization and
broad TOAS/Rhizome integration are not part of this acceptance.

## Exact implementation and runtime

- Root implementation: `b08895d843892da660068d65659c513cada9f3bc`; parent Stage 4 completion
  `38333cf9026f9f29cb10b59a6871b85d3948a2ed`.
- Final root acceptance revision: `3d861eaa4af5d34d5ae3e9e11ace56faed6261b7`
  adds the explicit on-disk overlay assertion before each teardown event.
- Pyzo implementation: `0797bb43363cd1152fea5dd1d2046ac05a81de2c`; parent
  `27b3aa04a8252a9a9a6b6858d07b691e6ddb7512`.
- Binding remains `b8d9c0a784db678227833ef8e545765a974ad4cb`, including its
  preexisting uncommitted packaging files. No binding changes or push.
- Python **3.12.13**, PySide6/Qt **6.11.1**; pinned local
  `pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl` with IPython.
  [Runtime record](workspace-debugger-2026-10-06/runtime.log).

## Accepted behavior and evidence

| Boundary | Executable proof |
| --- | --- |
| Durable owner/source overlays | Shared A/B document has independent enabled/disabled entries; same-owner native views agree; only each owner's paths/lines reach its kernels. Registry roundtrip without open views, pathless aliases, rename/Move identity, owner-only Fork copy, unavailable/reactivated sources, path reuse and explicit broken-entry discard have policy/native assertions. |
| Shared editing | Native insertion and authoritative undo move A/B overlays independently; frozen live-session snapshots remain unchanged. Durable line rebasing also follows edits for owners without open views. Deleted source lines remove their markers; rebasing follows line edits, without claiming semantic breakpoint relocation. |
| Real independent sessions | Two actual Python kernels stop at A line 3 and B line 4 of the same source. An A overlay edit affects the next session while the current session keeps its original snapshot. Stepping B advances B alone; selecting idle B cannot fall through to paused A. |
| Live and postmortem provenance | Separate session IDs and monotonically increasing frame-state sequences accompany fixed operation/shell/generation ownership. Wrong owners, generations, epochs and stale sequences are rejected. Two PM contexts originate from an unhandled exception and a handled exception captured through logging. Both execute code against their captured locals; NEXT/STEP/RETURN/JUMP/CONTINUE remain disabled. |
| Stale actions and queries | A captured stack action cannot act through foreign foreground focus. A same-shell old frame action and a held real query result are rejected after stepping. The kernel rejects a stale query before evaluating its side effect; the side-effect variable remains absent. Existing view/assignment/consumer/restart guards continue passing. |
| Source and indicators | Navigation uses session document identity and the session workspace's view, including retained dirty resources. Indicators affect only the owning foreground session's views. Missing sources stay unavailable; canonical path aliases resolve the existing identity. |
| Debugging closure | Actual visible live/PM confirmation dialogs warn about interpreter and captured stack loss. Workspace Cancel, failed manifest publication and fresh Cancel after failure preserve exact topology/resources/assignments/native contexts and both debug states, with zero unbind/close/terminate events. |
| Retain before termination | On-disk text, clean baseline, undo/redo and A view records are checked before every irreversible A event; durable overlays are checked in the same generation. Only A terminates. A actually exits; B keeps the same PID/context/assignment/PM state and executes another captured-frame command. |
| Resume and fresh process | A resumes the retained shared identity and independent overlays without reviving its interpreter. Quit then a new owned app process restores both owners' enabled/disabled overlays and dirty shared text. No old interpreter or captured stack is revived; source bytes remain unchanged. |

Final integrated probe: A PID **8315**, B PID **8321**; durable generation
`874eb686a8dd4ca0915fe373b319f749`. Two A editor-unbinds, A shell-close, then
A terminate were observed against that on-disk generation. The integrated proof
passes in **5.229s**, fresh-process restore in **0.786s**.
[Debugger and restart log](workspace-debugger-2026-10-06/debugger.log).

## Bounded repairs found during acceptance

The shared document adapter replaced native text while blocking Qt signals,
leaving native breakpoint blocks stale. Resource edits now rebase the durable
entries once for every owner, and native views rebuild markers after projection.
Active-session snapshots remain fixed. All local aliases of an untitled shared
resource receive its owner's entries.

Resume could leave an older pending checkpoint and historical retained descriptor
that later replaced its live membership. Close/resume now refresh the pending
snapshot; current live membership supersedes historical retained membership.
Workspace captures preserve complete session metadata and native frame geometry
for every owner. Startup applies metadata to already translated native pane IDs.
The fresh-process proof rejects restore warnings as well as lost overlays/views.

Logged exceptions now publish their captured operation provenance alongside the
traceback. A lost foreground shell disables its debugger controls without using
another shell. Canonical-path matching fixes `/var`/`/private/var` source aliases
that otherwise attempted duplicate registration. The task's pre-edit state map
records these observed states before their implementation changes.

## Verification and reproduction

**481 coordinated tests, 51 subtests, and all 15 live controls pass.** The
coordinated suite skips those 15 opt-in live cases plus the stock four-tab-side
expectation superseded by the pinned fork. Two existing Qt high-DPI deprecation
warnings remain. All 20 touched Python files compile; Ruff F and whitespace
checks pass. Full peer smoke passes in **10.759s**, maintained-fork legacy in
**7.170s**. The final all-live suite passes in **54.67s**.

Logs: [coordinated](workspace-debugger-2026-10-06/coordinated.log),
[all live](workspace-debugger-2026-10-06/live.log),
[peer](workspace-debugger-2026-10-06/peer.log),
[legacy](workspace-debugger-2026-10-06/legacy.log),
[source checks](workspace-debugger-2026-10-06/source-checks.log),
[smoke durations](workspace-debugger-2026-10-06/smoke.log).

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. \
  ./.codex-local/bin/uvt run --offline --python 3.12 \
  --with pytest --with PySide6 \
  --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl \
  --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs

RUN_LOCAL_RETENTION_ACCEPTANCE=1 RUN_LOCAL_EXECUTION_ACCEPTANCE=1 PYTHONPATH=. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest python -m pytest \
  spikes/peer_frames/test_local_retention_acceptance.py \
  spikes/peer_frames/test_local_execution_acceptance.py -q -s
```

Owned probes use isolated appdata, workspace/recovery directories and a command
server stub. Kernels are real; each phase has a 12-second deadline and the
harness owns a 35-second external deadline and process-group cleanup. Temporary
probe state is removed; root/Pyzo implementation and completion are separately
committed. No user interpreter or unrelated process is targeted.

This is macOS offscreen Qt acceptance. Physical window-manager/accessibility/
drag behavior and Windows/Linux acceptance remain Stage 7 debt. Legacy control
means this maintained fork's non-peer host, not pristine upstream. Stage 6 still
owns tool/config/project/history/affiliation isolation and capability fallbacks.
