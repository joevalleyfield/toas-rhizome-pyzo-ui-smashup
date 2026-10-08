# Native workspace restore lifecycle — 2026-10-07

Task [034](../../tasks/open/034-native-workspace-restore-lifecycle.md) is accepted
as the bounded native lifecycle follow-up to 033. The adapter recreates detached
or deleted floating targets before placement, and retired backends discard queued
native callbacks. Full 014 Stage 7 remains open.

## Exact implementation and runtime

- Root implementation: `c53e5aff84eb9b8d849d84700650179530735c8a`, parent
  `dfb0007a22ba64b08e0de4831953aa4f40c8bd9b`.
- Pyzo unchanged: `0e334f57de142cf4deeee4dd43b5b1453b9ad6f4`.
- Binding unchanged: `b8d9c0a784db678227833ef8e545765a974ad4cb`, parent
  `764eb4a4`; existing packaging/lockfile working-copy edits preserved.
- Embedded QtADS unchanged: `243aa54b4f131212ce02ce78b347a13cb3713736`.
  Separate QtADS reference remains `59d4730119466e02195f1a221a54386a9410b16f`.
- Local wheel: `pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl`.
- Python 3.12.13, PySide6/Qt 6.11.1, IPython 9.17.1, macOS 27.0.1 arm64;
  [runtime log](native-restore-2026-10-07/runtime.log).

Nothing pushed. No Pyzo or native dependency source changes.

## Reproduction and repairs

Thirty fresh debugger restores with hash seeds 0–29 pass on the unchanged
baseline, confirming that simple repetitions alone do not explain the recorded
intermittent failure. [Baseline replay](native-restore-2026-10-07/replay.log)
and its individual logs are retained.

The [minimal native probe](../../spikes/peer_frames/qt_native_restore_probe.py)
constructs A(one), B(two), then restores A(two), C(one). The initial ensure pass
moves one into C and empties A. QtADS immediately calls `finishDropOperation`,
unregisters A's container and clears its manager, while its wrapper remains valid
until deferred deletion. Realization subsequently reuses cached A and calls
`addDockWidgetToContainer` with a null manager. The unchanged adapter exits 139;
the trace prints `PLACEMENT peer-pane:two manager None` before the fault.
[Before](native-restore-2026-10-07/minimal-before.log),
[after](native-restore-2026-10-07/minimal-after.log).

This demonstrates the null-manager mechanism matching 033's native constructor
stack. The exact original debugger process had no Python stack or retained
fixture, so its particular layout ordering cannot be established independently.

`_ensure_frame` now checks wrapper validity and native manager ownership.
`_realize_frame` revalidates at entry because an earlier placement can detach a
later target. Replacement moves existing panes; it does not recreate their
content, document or kernel resources. No native-library repair is needed.

A separate verification cycle exposed queued synchronization after backend
close and manager deletion. [Failing full suite](native-restore-2026-10-07/coordinated.log)
records the invalid C++ manager access. Synchronization, settled notification,
area/focus signals and scheduling now check `_closing`, and repeated close is
idempotent. Retired timers clear flags without model adoption, native access or
observer notification; live behavior retains its existing controls.

## State coverage and verification

The pre-edit state/assertion tables and both repair cycles are recorded in
[034](../../tasks/open/034-native-workspace-restore-lifecycle.md).

- 288 permutation cases: six pane orders × six frame orders × four frame-ID
  patterns × two event/activation states. Exact layout before and after deferred
  deletion, registered manager ownership, zero hidden-root dock areas and no
  fatal projection destruction. No explicit activation uses the existing
  captured-live-pane fallback; explicit activation remains exact.
- Two cached-wrapper cases: detached pending deletion and already deleted.
  Neither stale target is dereferenced or reused.
- Two retirement cases: manager deletion pending/delivered, held sync/settled
  timers, late native focus/area signals and repeated close. Zero adoption or
  observer notification, flags cleared, no access to invalid native wrappers.
- Final coordinating/Pyzo suite: **591 passed, 348 subtests passed, 19 skipped**
  (18 opt-in controls plus one stock-backend capability case), two existing Qt
  deprecation warnings; [log](native-restore-2026-10-07/coordinated-final.log).
- Final process-owned retention/execution suite: **18 passed in 61.04s**,
  including the new minimal native probe, real debugger/kernel controls,
  fresh restore, tools, ingress and transactional closure;
  [log](native-restore-2026-10-07/live-final.log).
- **30 final fresh-process debugger restores**, seeds 0–29, from independent
  copies of one test-owned live-debugger fixture: no failures;
  [summary](native-restore-2026-10-07/replay-after.log),
  [fixture producer](native-restore-2026-10-07/after/seed.log),
  [first restore](native-restore-2026-10-07/after/restore-00.log),
  [last restore](native-restore-2026-10-07/after/restore-29.log).
- Four changed Python sources compile; Ruff F and trailing-whitespace checks
  pass; [log](native-restore-2026-10-07/source-checks.log).

The first permutation run incorrectly expected native capture to preserve an
unspecified active pane as `None`; existing capture selects a live pane. The
reduced [failure log](native-restore-2026-10-07/backend.log) preserves the first
failure and summary. Its corrected assertion passes without a production
activation change. Unrelated formatting changes were removed before commit.

## Remaining compatibility gate and correction

Final serial smoke controls: legacy passes in 7.68s; peer completes in 10.99s,
including no-QMainWindow host, editor lifecycle, layout, ordinary live-debug and
postmortem checks. Its older affinity subprobe times out at `wait-affinity-seed`
with second identity `Error evaluating: peer_kernel_identity` and cwd `/Users/tim`.
[Summary](native-restore-2026-10-07/smoke-complete.log),
[peer](native-restore-2026-10-07/peer.log),
[legacy](native-restore-2026-10-07/legacy.log).

The same warning exists in accepted [032 peer log](workspace-tools-2026-10-06/peer.log)
and [033 peer log](workspace-ingress-2026-10-07/peer.log). Their descriptions of
full peer smoke success were too broad: process completion did not reject this
printed timeout. Dedicated live workspace kernel/ownership controls still pass.
Record this as the next compatibility follow-up candidate: reproduce the second
shell's affinity seed and make smoke completion fail when any subprobe times
out. No speculative kernel/smoke behavior change belongs to this native repair.

Offscreen test-owned processes do not accept physical OS/window-manager behavior,
Windows/Linux, unmodified vanilla Pyzo, representative scale, the final census or
all integrated restart requirements. File Move/Fork UX and September deferrals
remain separate. The bounded native lifecycle repair is complete.

## Reproduction commands

```sh
QT_QPA_PLATFORM=offscreen PYTHONFAULTHANDLER=1 PYTHONPATH=. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with PySide6 \
  --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl \
  python spikes/peer_frames/qt_native_restore_probe.py

RUN_LOCAL_RETENTION_ACCEPTANCE=1 RUN_LOCAL_EXECUTION_ACCEPTANCE=1 \
PYTHONFAULTHANDLER=1 PYTHONPATH=. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest python -m pytest \
  spikes/peer_frames/test_local_retention_acceptance.py \
  spikes/peer_frames/test_local_execution_acceptance.py -q -s
```

For the repeated restores, call `run_owned_probe("workspace-debugger", fixture,
probe=qt_workspace_debugger_probe.py, deadline=35)` once. Keep the fixture alive,
copy it into a new temporary directory for each seed 0–29, then call the same
probe with phase `debugger-restore`, `PYTHONHASHSEED=str(seed)` and
`PYTHONFAULTHANDLER=1`. Require `WORKSPACE DEBUGGER RESTART COMPLETE` on every run.
Each launch owns its process group and external deadline; no user appdata/server
is used.
