# Experiment 008 hidden-`QMainWindow` dependency inventory

## Scope and conclusion

This inventory describes the peer-frame Pyzo integration at coordinating
commit `45c9a75` and Pyzo commit `ca8dcd5`. It traces direct `pyzo.main`
references, inherited `QMainWindow` operations, and services still constructed
on the hidden host.

QtADS does not require the hidden `QMainWindow` in peer mode. Its manager is
parentless and hidden, all user-visible frames are floating peer containers,
the macOS menu is application-owned and parentless, and status is projected
directly into peer frames. The remaining hidden-main dependency is a Pyzo
service-location and compatibility problem.

The hidden host is still required by four coupled Pyzo mechanisms:

1. the legacy menu/action graph and its shortcuts, shell toolbar actions, and
   Run-menu method calls;
2. geometry, layout, and named-view persistence encoded through
   `QMainWindow.saveState()` and `restoreState()`;
3. application shutdown and restart implemented as a window `closeEvent`;
4. dialogs and tool widgets that use `pyzo.main` as their parent or placement
   controller.

Removing the widget before replacing those mechanisms would regress commands,
Run/Debug, persistence, lifecycle negotiation, or dialog modality. Keeping it
temporarily does not impose a user-visible main-frame topology, but it remains
migration scaffolding rather than the desired application model.

## Dependency map

| Dependency | Principal evidence | Current peer behavior | Peer risk | Required ownership seam |
| --- | --- | --- | --- | --- |
| Menu and action graph | `main.py` builds all menus on `self.menuBar()`; `menu.py` reaches `pyzo.main.menuBar()` for Run and shortcut editing; `shellStack.py` copies hidden Shell-menu actions into shell toolbars | Application Quit, Restart, and status visibility are projected to peer chrome; hidden menu objects still supply other behavior | **Removal blocker.** Most menus are unavailable from peer frames, window-scoped shortcuts may depend on a hidden owner, and shell/debug controls consume actions by widget ancestry | Application command registry plus menu/toolbar projections. Context menus and shell controls call command services by stable identity rather than finding a `QMenu` |
| Run and Debug routing | Editor context menus find `RunMenu` under `pyzo.main.menuBar()` and call private `_runFile()`/`_runSelected()` methods; shell debug actions are read from the hidden Shell menu | Existing service wiring works in smoke tests, but action ownership and multiple-kernel targeting remain legacy | **Removal and product blocker.** The menu is acting as the Run service, and `getCurrentShell()` remains an ambiguous execution target with multiple kernels | Run/debug service with explicit editor, shell/kernel, launch configuration, and captured-frame identities; action projections invoke that service |
| Workspace layout persistence | Startup calls hidden-main `restoreGeometry()`/`restoreState()` twice; `getWindowState()` serializes hidden-main geometry/state; `_start.saveConfig()` invokes it; `ViewManager` saves and restores the same blobs | Peer topology exists only in `WorkspaceModel`; normal shutdown still stores hidden-window state, not peer frames | **Removal blocker and data-model mismatch.** Named views and restart cannot faithfully restore peer frames | Workspace/session persistence stores application frame/group/pane topology and per-frame geometry. Named views operate on that schema, scoped for multi-workspace use |
| Application shutdown | Legacy mode retains `MainWindow.closeEvent()`; peer Quit, Restart, command-line shutdown, test shutdown, and final-frame policy call an application coordinator | Peer exit negotiates one `CloseReason.APPLICATION` transaction, commits pane cleanup once, attempts every ordered service cleanup, and then quits or replaces the process. Cancellation is pre-commit; post-commit failures are logged and cannot imply rollback | **Dialog-parenting follow-up.** The hidden window no longer triggers peer shutdown, but explicit active-peer ownership for the optional global confirmation remains unresolved | Move the coordinator off `MainWindow` once an application controller exists; provide an active-context window for confirmation and fatal reporting |
| Dialog ownership and modality | Dirty-file prompts and quit confirmation use `QMessageBox(pyzo.main)`; the Views dialog uses `pyzo.main`; tool constructors receive `pyzo.main` | Some dialogs happen to surface on macOS, but their logical parent is hidden and not the invoking peer | **High UX risk.** Modality, z-order, screen placement, and focus restoration can target an invisible host, especially on Windows/Linux | Active-context window provider selects the invoking peer; application-modal dialogs use explicit application modality when no frame is appropriate |
| Tool construction and placement | `ToolManager` creates `ToolDockWidget(pyzo.main)`, constructs tool widgets with `pyzo.main`, and calls main-window add/split/remove methods | Peer branches already delegate placement and removal into the peer workspace/backend; Qt reparents tool content into the dock | **Medium coupling.** Placement works, but creation and lifetime APIs expose the hidden host and legacy `QDockWidget` path | Tool service accepts a pane factory, lifecycle policy, and workspace placement service. Widget parenting uses the pane content host or application lifetime object |
| Editor and shell hosts | `EditorTabs(self)` and `ShellStackWidget(self)` are initially created from the main host; manager facades are parented to it | QtADS reparents each content host into its dock. Editor/shell state and focus survive peer moves | **Low immediate risk.** This is lifetime scaffolding, not visible topology, after reparenting | Application/service lifetime owner, normally `QApplication` or an application controller, creates pane content without a workspace-window parent |
| Status | Historical callers use `pyzo.main.statusBar()` | Peer mode supplies `PeerStatusService`; every peer frame receives a status projection; no hidden `QStatusBar` exists | **Resolved compatibility seam.** The method name remains, but ownership no longer requires `QMainWindow` | Preserve the application-owned status state and compatibility facade until callers can inject the service directly |
| Title and running icon | Editors call `setMainTitle()`; shell state calls `setWindowIcon()` on `pyzo.main` | Updates affect the hidden host. Peer frame titles currently derive from dock titles; running state has no equivalent peer indication | **Visible information loss.** A hidden icon/title cannot communicate active document or busy/debug state | Application metadata plus frame/pane chrome projections. Busy/debug indicators must be scoped to their shell/kernel rather than presented as one global kernel state |
| Appearance and theme | Menu callbacks call `pyzo.main.setQtStyle()`; theme changes call `restart()` | Qt style application is process-global and works despite living as a main-window method | **Low operational risk, wrong owner.** Restart remains coupled to lifecycle | Application appearance service owns palette/style/theme; lifecycle service handles required restart |
| Startup splash and geometry | `MainWindow.__init__()` resizes, restores, shows, paints, and installs a splash as central widget before populating peers, then hides itself | The host may briefly exist as a visible startup window and performs irrelevant hidden geometry restoration | **Peer-model leak and startup complexity.** It is not needed after initialization | Independent splash/startup controller creates services, restores workspace sessions, then presents peer frames directly |
| Developer screenshot helpers | `screenshotExample()` resizes `pyzo.main`; `_screenshot()` grabs its `winId()` | Captures the hidden host in peer mode | **Low product risk.** Utility is incorrect for peers | Capture an explicitly selected peer frame or the full workspace frame set |

## Direct-reference census

The source contains 47 direct `pyzo.main.<member>` calls across 13 files. The
most frequent are:

- `close`: 7;
- `statusBar`: 6;
- `menuBar`: 6;
- `restart`: 4;
- `saveWindowState`: 3;
- `setWindowIcon`, `setMainTitle`, `restoreState`, `restoreGeometry`, and
  `addAdsDockWidget`: 2 each.

The concentration is more informative than the raw count. `menu.py` has 13
direct calls, `tools/__init__.py` and `views.py` have 9 each, and the remaining
calls cluster around lifecycle, status compatibility, editor title updates,
and shell debug state.

## What can remain temporarily

The name `pyzo.main` can remain as a compatibility facade while migration is in
progress, provided callers do not depend on it being a visible frame or a
`QMainWindow`. Likewise, a hidden QObject may own service lifetimes. Neither
requires a hidden workspace window.

The following current uses are therefore tolerable scaffolding during the
feasibility spike:

- lifetime parenting that is replaced when content enters a dock;
- the status compatibility method, whose state and rendering are already
  application-owned;
- global style initialization;
- the lifecycle coordinator methods temporarily hosted on `MainWindow`; peer
  Quit and Restart no longer close that hidden widget.

The hidden menu graph and hidden-main persistence cannot be mistaken for final
architecture merely because current smoke tests pass.

## Removal conditions

The `QMainWindow` subclass can cease to be the application host when all of the
following are true:

- every user command needed by editor, shell, file browser, Run/Debug, tools,
  settings, and help is application-owned and projectable into peer chrome;
- shell toolbars and editor context menus invoke command IDs or services rather
  than dereferencing hidden menu widgets;
- peer workspace/session state, including frame geometry, replaces
  `QMainWindow.saveState()` blobs and named views use that state;
- Quit and Restart are application lifecycle operations with active-peer dialog
  parenting; transactional pane/service cleanup is complete, while parenting
  remains open;
- tool and pane factories no longer require a main-window parent or its
  add/split/remove methods;
- application, frame, pane, shell, and debugger indicators have explicit
  projection scopes;
- startup creates peer frames without showing, painting, restoring, or later
  hiding a central-widget host.

## Open questions exposed by the inventory

- Should `pyzo.main` become a compatibility alias for an application controller,
  or should callers migrate directly to narrowly scoped services?
- Can Pyzo's existing `QMenu` classes be adapted as command projections, or is
  their use as behavior-bearing services too deep for a bounded migration?
- What do Pyzo named views mean with multiple workspaces: one workspace layout,
  an application-wide collection of workspace layouts, or a reusable layout
  template?
- Which peer owns an application-modal prompt when the initiating operation is
  global rather than pane- or frame-scoped?
- How should document title, shell busy state, debugger state, and execution
  affinity divide between pane, frame, workspace, and application chrome?
- Should a peer-mode startup splash be application-global, attached to the
  first restored workspace, or omitted?

These are ownership questions rather than evidence that QtADS requires a main
window. No current finding requires exposing QtADS's privileged root to the
user.
