# Experiment 012: Remove the hidden Pyzo main window

## Status

In progress. Slices 1–3 are accepted. Slice 4a, tool construction and dialog
ownership, was accepted on 2026-07-18. Metadata projection plus the remaining
appearance/restart callers are next; no toas/rhizome integration is in scope.

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
- The 150-test coordinating suite remains green with only the three expected
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

### Slice 2a — shell toolbar enablement regression

Accepted on 2026-07-18 at Pyzo revision `a3c26a5`. The shell toolbar still
borrows actions from the hidden Shell menu pending the broader command-service
migration, but those actions no longer remain disabled after startup.

`ShellGroupManager` now forwards a current-shell change emitted by an already
active host instead of returning early through `setActiveHost()`. A focused
test proves the startup sequence reports both the initially empty host and its
subsequently created first shell. The real Pyzo smoke asserts that every
ordinary Shell-menu action is present and enabled in every shell toolbar. It
passed in peer mode against the local four-side binding fork and in the legacy
control. The full 147-test coordinating suite also passed with three expected
published-wheel skips; compilation and whitespace checks passed.

### Slice 2b — application-owned shell commands

Accepted on 2026-07-18 at Pyzo revision `448cfd5`. A non-widget
`ShellCommandService` now owns stable command identities, ordinary pane-shell
targeting, explicit debugger execution-shell targeting, invocation, breakpoint
clearing, and dynamic enablement. `ShellCommandProjector` creates independent
actions for the Shell menu, shell context menus, and every shell toolbar.
`ShellStackWidget` no longer reads `_shellActions` or `_shellDebugActions` from
`pyzo.main.menuBar()`, and toolbar actions are deliberately distinct from the
temporary hidden-menu projections.

Focused tests cover ordinary invocation, disabled state without a shell,
post-mortem start, debug-mode transitions, selected-line jump, stop, and
breakpoint clearing. The real smoke caught and fixed context-menu target
assignment after menu construction, then replaced its last direct private
`ShellMenu._debugAction()` call with the application service. The final peer
run against the local four-side fork completed editor/shell/tool, lifecycle,
movement, zero-frame, Run/live-debug, post-mortem, and multi-kernel workflows.
The legacy control and all 147 coordinating tests passed with three expected
published-wheel skips; compilation and whitespace checks passed.

### Slice 2c — application-owned editor execution commands

Accepted on 2026-07-18 at Pyzo revision `78af7d6`. A non-widget
`RunCommandService` now owns selection, current-line, cell, file, main-file,
and script execution. It resolves the explicit execution shell directly and
is exposed by the peer application controller. The Run menu is now only an
action projection, while editor and editor-tab context menus call the service
without looking through `pyzo.main.menuBar()`, `_menumap`, or
`findChild(RunMenu)`. Tab-context execution also targets the clicked editor
without depending on whichever editor happens to be current.

Focused tests cover current-editor execution, change-directory propagation,
explicit execution-shell use, and clicked-tab targeting when no current editor
exists. The real peer replay against the local four-side fork passed ordinary
Run/live debug, post-mortem re-entry, and multi-kernel execution affinity in
addition to the editor, shell, tool, lifecycle, movement, and zero-frame
matrices. The published-wheel legacy control passed, as did all 147
coordinating tests with the three expected capability skips. Python
compilation, direct-reference checks, and both repository whitespace checks
passed. The remaining Slice 2 work is to project the other application menus
into peer chrome and migrate their behavior owners.

### Slice 2d — complete peer menu projection

Accepted on 2026-07-18 at Pyzo revision `f245263`. Peer mode now constructs the
complete File, Edit, View, Settings, Shell, Run, Tools, and Help menu graph in
peer chrome through the application command projector. It no longer builds any
actions on the hidden `QMainWindow.menuBar()`, avoiding duplicate application
shortcuts and removing that menu bar as a behavior owner. macOS retains one
parentless shared native menu bar; Windows and Linux retain independent
per-frame menu bars with reserved frame chrome.

The generic projector can now accept a complete menu-bar builder and route
registered commands into named menus. Peer Quit and Restart are injected into
File and status visibility into View, with lifecycle invocation routed through
the non-window application controller. Key-mapping inspection, appearance,
status, view-manager parenting, and advanced-settings restart paths select the
peer application boundary when present while preserving explicit legacy
fallbacks.

A focused projector test covers full menu construction, named command routing,
and primary-menu discovery. The real peer replay asserted the complete ordered
menu set, an empty hidden menu bar, application-owned lifecycle invocation, and
all previously accepted editor, shell, tool, lifecycle, movement, Run/debug,
post-mortem, and multi-kernel workflows. The published-wheel legacy control
passed unchanged. The coordinating suite now passes all 148 tests with three
expected capability skips; compilation, direct-reference checks, and both
repository whitespace checks passed.

### Slice 3 — workspace-session persistence and named views

Accepted on 2026-07-18 at Pyzo revision `1516692`. Peer mode now persists a
versioned application session containing the authoritative workspace layout,
active pane, frame/group/pane topology, tab sides, loaded tools, and each peer
frame's geometry. Startup and normal-view saving use this session boundary and
skip `QMainWindow.saveState()`, `restoreState()`, `saveGeometry()`, and
`restoreGeometry()` entirely; the legacy path retains its existing Qt blob
workarounds.

Named peer views now store and apply complete workspace-session snapshots.
Restoration is transactional across tools, topology, and geometry, with the
previous session restored after a failed target restore. Invalid schemas and
geometries are rejected without mutation. Legacy named views remain listed but
are explicitly refused in peer mode until the user saves them again, preserving
a bounded fallback without interpreting main-window blobs as peer topology.

Focused tests cover restoration into a fresh service/workspace instance (the
restart boundary), geometry and tool round trips, invalid-state rollback,
named-view save/apply, and legacy-view refusal. The real peer smoke collapsed a
live shell frame into an editor frame, reconstructed the original topology and
all frame geometries, rejected an invalid session without mutation, and then
completed the editor, shell, tool, lifecycle, movement, zero-frame, Run/debug,
post-mortem, and multi-kernel matrices. Test-mode recent-file and recovery state
were isolated so interrupted prior runs cannot contaminate this replay. The
published-wheel legacy control passed unchanged. The coordinating suite now
passes all 150 tests with three expected capability skips; compilation,
direct-reference checks, and both repository whitespace checks passed.

### Slice 4a — tool workspace and visible dialog ownership

Accepted on 2026-07-18 at Pyzo revision `0af03aa`. `ToolManager` and
`ToolDockWidget` now receive an explicit `ToolWorkspaceAccess` instead of using
`pyzo.main` as widget parent, dock-manager lookup, placement controller, reload
placeholder owner, or close path. Tool content is owned by its actual dock, and
the same interface preserves legacy placement through its ordinary main window.
The source-structure tool also projects messages through the application status
service in peer mode.

The peer controller now exposes `DialogParentAccess`; editor file prompts,
live-shell close confirmation, application-exit confirmation, and recovery
failure prompts resolve the visible active peer instead of the hidden host or an
unowned global dialog. Focused controller coverage verifies both boundaries.

The real replay exposed a stale native focus notification after workspace
restoration: tool content with correct dock ownership could reassert the last
focused tool over the saved active shell. Layout restoration now explicitly
projects native window/content focus to the saved active pane and suppresses
reverse adoption until QtADS reaches its settled-layout synchronization point.
Focused backend coverage preserves normal user focus adoption while asserting
that restored logical and native layouts agree.

The final real peer replay passed workspace-session restoration, movement,
clean/dirty lifecycle, independent shell, zero-frame recreation, Run/live debug,
post-mortem re-entry, and multi-kernel affinity without callback failures. The
legacy control passed unchanged. All 150 coordinating tests passed with the
three expected capability skips, and both repository whitespace checks passed.
The remaining Slice 4 work is metadata projection and the residual global
appearance/theme/restart callers.

## Known portability obligations

- Exercise active-peer and application-modal dialog ownership natively on
  Windows and Linux before production adoption.
- Verify per-frame menus/shortcuts, taskbar/application lifetime, restart, and
  zero-frame policy on both platforms.
- Treat those as the existing Experiment 010 release gate, not as permission
  to retain a hidden main window.
