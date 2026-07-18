# Experiment 012: Remove the hidden Pyzo main window

## Status

In progress. Slice 1, the peer application controller and compatibility
boundary, was claimed on 2026-07-18. Work proceeds in the ordered slices below;
no toas/rhizome integration is in scope.

## Objective

Start peer-mode Pyzo without constructing a hidden `QMainWindow`. Replace the
remaining behavior, persistence, parenting, lifetime, and metadata assumptions
with application-owned services while preserving the accepted editor, shell,
file-browser, Run/Debug, post-mortem, lifecycle, layout, and command workflows.

`pyzo.main` may remain temporarily as a compatibility alias for an application
controller, but peer-mode callers must not require it to be a widget, window,
menu owner, dock owner, or dialog parent. Legacy Pyzo may retain `MainWindow`
on its non-peer startup path.

## Dependencies

- Experiment 005 accepts Pyzo with hidden-main removal as a completion gate.
- Experiment 008 inventories the remaining hidden-main dependencies.
- Experiments 004 and 009 provide the regression workflows for debugger and
  lifecycle behavior.

## Ordered implementation slices

### 1. Application controller and compatibility boundary

- Introduce the peer-mode application controller/lifetime owner without
  changing the legacy startup path.
- Define narrow services or facades for lifecycle, active-peer lookup, status,
  appearance, execution targeting, and workspace access.
- Make `pyzo.main` compatibility explicit and test that peer code does not rely
  on `QMainWindow` inheritance.
- Keep the hidden host temporarily until later slices remove every remaining
  widget dependency; commit this foundation independently.

### 2. Commands, menus, toolbars, and Run/Debug

- Remove behavior lookup through `pyzo.main.menuBar()`, `_menumap`, and
  `findChild(RunMenu)`.
- Register the editor, shell, file-browser/tool, Run/Debug, settings, view, and
  help commands needed by the accepted workflow in application-owned services.
- Project equivalent menus/actions into peer chrome using active context and
  explicit execution target state.
- Route editor context menus and shell toolbars through command IDs/services,
  not hidden `QMenu` ancestry.

### 3. Workspace persistence and named views

- Persist peer frame/group/pane topology, tab side, active context, and
  per-frame geometry through the application workspace/session schema.
- Stop writing peer-mode `QMainWindow.saveState()` and geometry blobs.
- Define a named view as a reusable complete peer-workspace layout snapshot;
  preserve a bounded, explicit migration/fallback for legacy view data.
- Verify save, restart/restore, named-view apply, invalid-state fallback, and
  retained dirty-buffer recovery together.

### 4. Dialogs, tools, metadata, and appearance

- Parent pane/frame operations to the invoking active peer and use explicit
  application modality for global operations.
- Construct tool and pane content through application lifetime/pane factories,
  without `pyzo.main` as widget parent or dock-placement controller.
- Project document title, shell busy/running state, debugger state, and
  execution target at the correct pane/frame/application scope.
- Move global style/theme and restart behavior behind application services.

### 5. Startup cutover and host deletion

- In peer mode, create services and restore/create ordinary peer frames
  directly; do not show, paint, restore, hide, or retain a central-widget host.
- Omit the legacy main-window splash in peer mode unless an application-owned
  splash is demonstrated not to affect frame topology or lifecycle.
- Ensure Quit, Restart, command-server shutdown, final-frame policy, and fatal
  startup reporting operate through the application controller.
- Delete the peer-mode hidden-host compatibility path and assert that no
  `QMainWindow` instance exists during or after peer startup.

## Acceptance criteria

- Peer-mode startup creates zero `QMainWindow` instances and every visible
  workspace window is an ordinary peer QtADS container.
- `pyzo.main` in peer mode is either absent or a non-widget compatibility
  controller; direct callers do not require window/menu/dock APIs.
- The complete Experiment 005 replay passes with real kernels: editor, shell,
  file browser, Run/live debug, post-mortem frame selection and execution,
  multi-kernel targeting, lifecycle, pane movement, zero-frame recreation,
  menus, commands, status, and shutdown.
- Peer workspace and named-view persistence restore topology and geometry
  without `QMainWindow.saveState()`/`restoreState()`.
- Dirty-document and live/debugging-shell prompts use the invoking peer or
  explicit application modality and restore focus correctly.
- Tool creation/placement and metadata projection require no hidden widget.
- The legacy non-peer Pyzo control remains green.
- The 147-test coordinating suite remains green with only the three expected
  published-wheel capability skips.
- Source checks reject new peer-mode dependencies on `QMainWindow`, hidden
  `menuBar()` behavior lookup, or hidden-widget dialog parenting.

## Allowed write surface

- `deps/pyzo/pyzo/` source and tests required for the peer controller and
  service migrations.
- Root `spikes/peer_frames/` contracts, projectors, persistence, and tests only
  where an application/backend seam must be extended.
- Root evidence, planning, and this task artifact.
- No toas/rhizome implementation and no QtADS or binding fork changes unless a
  new dependency-level blocker is first recorded with a minimal reproduction.

## Completion evidence

For each slice, record the removed dependency class, replacement owner, focused
tests, real peer smoke result, legacy control result where relevant, and exact
root/Pyzo revisions. Final evidence must include a runtime census of top-level
widgets proving no peer-mode `QMainWindow`, persistence round trips, dialog
ownership observations, the complete Experiment 005 replay, and an updated
direct-reference census.

### Slice 1 — application controller and compatibility boundary

Accepted on 2026-07-18 at Pyzo revision `3f1e156`. Peer mode now creates a
`PeerApplicationController` parented to `QApplication`, with named workspace,
active-peer, status, lifecycle, appearance, and execution-target facades. It is
not a widget and does not proxy `menuBar()`, `statusBar()`, or arbitrary
`QMainWindow` APIs. `legacy_host` is the sole explicit bridge to the temporary
host, and legacy mode leaves `pyzo.application` unset.

The focused controller test passed by direct invocation under the cached Qt
runtime; the offline cache did not contain the selected pytest runner. Python
compilation and both repository whitespace checks passed. The coordinating
suite passed all 147 tests with three expected published-wheel skips. The real
peer smoke passed the controller runtime assertions, editor/shell/tool routing,
lifecycle and movement matrices, zero-frame recreation, Run/live debug,
post-mortem re-entry, and multi-kernel execution affinity. The legacy Pyzo
control also passed. The first real assertion exposed and fixed a stale bound
dictionary lookup so active-peer resolution now reads the backend's current
frame map after settled-layout adoption.

## Known portability obligations

- Exercise active-peer and application-modal dialog ownership natively on
  Windows and Linux before production adoption.
- Verify per-frame menus/shortcuts, taskbar/application lifetime, restart, and
  zero-frame policy on both platforms.
- Treat those as the existing Experiment 010 release gate, not as permission
  to retain a hidden main window.
