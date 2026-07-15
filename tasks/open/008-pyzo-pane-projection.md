# Experiment 008: Project Pyzo surfaces as application-owned panes

## Status

In progress. Application Quit, distinct close commands, platform menu
ownership, dynamic command synchronization, and peer status/focus projection
are complete. Hidden-main dependency inventory is the currently claimed slice;
deeper run/debug validation remains.

## Objective

Adapt Pyzo's editor, shell, file browser, and run/debug surfaces to the peer-
frame contract while keeping their state owned by application services rather
than frames or QtADS containers.

## Dependencies

- Experiment 006 defines the contract.
- Experiment 007 establishes a usable QtADS adapter or a bounded blocker.
- Experiment 003 provides reusable Pyzo integration evidence.

## Acceptance criteria

- Editor, shell, file-browser, and run/debug panes are created and identified
  through application-level pane descriptors.
- Any of those pane types can bootstrap a new peer frame.
- Moving, tabbing, splitting, floating, and re-docking a pane preserve its
  document, interpreter, tool, or debugger identity.
- Pyzo services locate panes by application identity and active context rather
  than by a distinguished main window or central widget.
- Menus, commands, status, and focus follow the active frame sufficiently to
  operate from every visible peer frame.
- Existing smoke coverage for independent editors, shells, tools, and debugger
  routing remains green through the adapter.
- Stock QtADS owns and renders docking overlays in the peer-frame path. Pyzo
  does not install, replace, or paint a parallel drop guide.

## Allowed write surface

- The local Pyzo project surface under `deps/pyzo` or its chosen fork/worktree.
- The peer-frame adapter and integration tests.
- Root-level integration notes and this task artifact.

## Completion evidence

Record the Pyzo ownership assumptions removed or wrapped, the demonstrated pane
matrix, verification commands, and any remaining main-window dependencies.

## Progress evidence

### Real Pyzo peer-frame mode

The local Pyzo fork now has an opt-in `PYZO_PEER_FRAMES=1` path. In that mode:

- Pyzo's `QMainWindow` remains a hidden application-service host rather than a
  visible workspace owner.
- A parentless, hidden, empty QtADS manager is owned by the coordinating
  peer-frame backend.
- Real `EditorTabs`, `ShellStackWidget`, and `ToolDockWidget` instances register
  as application panes and begin in visible peer floating frames.
- Editor and shell service facades retain their existing document, focus,
  debugger-routing, and interpreter identities.
- Tools route through the same peer placement seam; the file-browser smoke
  test loads and closes successfully.
- The previous main-window integration remains unchanged when the environment
  flag is absent.

The peer path deliberately does not instantiate `_AdsWindowOrderTracker`, the
main-container z-order override, `_AdsDropGuideController`, or `_AdsDropGuide`.
Stock QtADS owns both native overlays. The peer-mode smoke test asserts that the
manager has no parent and no root dock areas, every visible frame is a floating
container, both native overlays become visible, and no application-painted
guide exists.

Verification passed on macOS with Pyzo 4.21.0, CPython 3.12.13, and PySide6
6.11.1:

- Peer-mode Pyzo source smoke: editors, debugger routing, file-browser tool,
  native overlay ownership, and independent shells passed.
- Legacy Pyzo integration control: foreground ordering, editors, debugger
  routing, tool container, replacement-guide control, and shells passed.
- Peer-frame contract/backend suite: 26 tests passed.
- Python compilation and `git diff --check` passed.

### Native interaction evidence

The real Pyzo peer mode was exercised interactively with editor, shell, and
tool panes. The user reported that docking and native QtADS overlay rendering
behaved as expected, including overlapping peer frames. No missing, duplicated,
or flashing guide was observed.

The pass also clarified a stock QtADS interaction rule:

- Dropping a frame layout on the center/tab target flattens all incoming panes
  into the destination tab group.
- Dropping the same frame on an edge target preserves its internal layout as a
  nested split.

The behavior is consistent with the two target meanings and should be treated
as user-facing docking semantics rather than a Pyzo defect.

### Remaining slice

- Application Quit and the status-visibility bootstrap command are projected
  into every peer frame. The rest of Pyzo's menus and commands still live on
  the hidden `QMainWindow`.
- The projector now has explicit shared-native and per-frame menu policies;
  broader Pyzo menu content remains.
- Close Pane, Close Group, and Close Frame have distinct application command
  routes, but are deliberately not exposed in live Pyzo until Experiment 009
  installs dirty-editor and running-shell lifecycle policies.
- Run/debug and post-mortem behavior retains the existing service wiring but
  still needs end-to-end interactive validation through peer-frame moves.
- Tool close buttons are conservatively disabled in peer mode until Experiment
  009 supplies application-level close negotiation.

### Peer status and focus projection

Status is now application-owned state projected as host-level chrome into every
existing and future peer frame. The projection covers transient messages,
editor cursor position, persisted visibility, frame creation/destruction, and
zero-visible-frame state. A shared edge-reservation seam lets per-frame menu and
status chrome coexist without either projector overwriting the other's QtADS
container margins. The hidden `QMainWindow` no longer owns a `QStatusBar` in
peer mode; a compatibility service preserves Pyzo's existing `statusBar()`
callers and timeout behavior.

The first live pass exposed a bootstrap gap when the persisted status setting
was hidden but broader Pyzo menus were not yet projected. The application-owned
`view.status-bar` command now appears beside Quit and synchronizes its checked
state across all peer projections.

Focus inside pane content now maps back to application pane identity rather
than depending only on QtADS focused-dock or legacy inner-tab signals. This is
essential for document-level peer panes: after opening a second Python file,
clicking back into the first editor again selects its `EditorGroupManager`
host, workspace context, and cursor-status source. Shell focus similarly
selects its shell service host; tool focus updates workspace context without
discarding the last editor identity. Temporary non-pane focus remains inert.

Focus is explicitly not execution affinity. The globally replicated status
snapshot contains no kernel or execution-target field, and focus adoption does
not render/rebuild topology. Multiple-kernel target selection, visible affinity,
and cross-workspace resource transfer are recorded as Experiment 004 run/debug
acceptance rather than silently treating Pyzo's current-shell service as the
final product model.

Automated evidence:

- 60 peer command/contract/backend/status cases pass with three intentional
  stock/fork capability skips.
- Real Pyzo peer smoke passes editor, debugger document routing, file-browser
  tool context, native overlays, projected status, descendant focus routing,
  independent shells, and clean shutdown.
- Legacy Pyzo control smoke remains green.

Manual macOS evidence: status chrome appeared in every peer frame after using
the projected visibility command. Cursor movement and source-structure status
updates appeared everywhere. With two Python documents open, alternating focus
between their editor contents correctly restored status tracking to the focused
document. The Pyzo integration commit is `ca8dcd5`.

### Application-owned command seam

`spikes/peer_frames/commands.py` now defines a toolkit-neutral, ordered
`CommandRegistry`. The application registers each immutable descriptor once;
descriptors carry a stable ID, base and optional context-dependent label,
enabled/checked predicates, shortcut strings, and a handler. State and
invocation resolve against a fresh `ActiveContext`, and disabled invocation is
side-effect free. No descriptor or registry stores a `QMainWindow`, peer frame,
QtADS manager, dock container, or action object.

`WorkspaceModel.resolve_active_context()` maps the active pane identity to its
application-owned `PaneDescriptor`, frame ID, and group ID. Tests prove that
the context follows the pane through frame creation, center merge, activation,
and floating, while command labels, enabled state, checked state, and handlers
follow whichever pane is active at query/invocation time. Registration order,
duplicate IDs, empty IDs, and unknown command IDs are covered.

The combined command, contract, and QtADS adapter suite passes 39 cases with
one intentional stock-only skip. Python compilation and `git diff --check`
also pass. The implementation commit is `3543f2d`.

### Application Quit projection

`QtAdsCommandProjector` consumes selected application command IDs and projects
one action into every existing and future QtADS peer frame. Projection is
idempotent, removes destroyed-frame tracking, leaves native-menu frame layouts
untouched, and tags actions with their stable application command ID. A
non-native projection parents an equivalent menu bar to each frame for the
later Windows/Linux path.

Peer-mode Pyzo registers `application.quit` before creating its first frame.
Every projected Quit action delegates to `pyzo.main.close()`, retaining Pyzo's
existing confirmation, dirty-editor veto, state/history persistence, command
server, kernel, shell, tool, thread, backend, and application shutdown path.
Tests also prove that invoking a refusing handler does not mutate pane or frame
topology, and that detaching the only group preserves one application pane in
one peer frame without contaminating the private QtADS root.

The accepted macOS manual pass established that Quit remains available after
moving among peer frames and exits the application. Under the unbundled
`pyzolauncher.py` source run, Cocoa continues to render the process-derived
label `Quit pyzolauncher.py` despite Qt's application and display names both
being `Pyzo`; this is recorded as cosmetic packaging/process-name behavior and
does not block command ownership or shutdown acceptance.

Final verification passed both peer and legacy Pyzo source smoke tests, all 44
command/contract/backend cases with one intentional stock-backend skip, Python
compilation, and `git diff --check`. The coordinating implementation is
`488ce39`; the Pyzo integration is `7dcf57a`.

### Distinct close scopes

The application command seam now defines stable `workspace.close-pane`,
`workspace.close-group`, `workspace.close-frame`, and `application.quit` IDs.
Pane, group, and frame handlers resolve a fresh active context when invoked;
Quit remains the sole route to application shutdown. Repeated close invocations
therefore target the newly active scope, like repeated browser-tab closure, and
become disabled when no corresponding context remains.

The workspace contract adds `CloseReason.GROUP`, transactional
`request_close_group()`, and a matching backend request event. Closing a group
removes exactly its panes; closing the sole group may remove its frame but never
sets `shutdown_requested`. Existing refusal and confirmation logic is shared by
all three topology scopes, so no partial group or frame close can commit.

QtADS tests project all four command IDs as separate actions and assert that
only application Quit receives Qt's `QuitRole`. Live Pyzo continues to project
only Quit: its real peer panes still use permissive default close policies, so
exposing the other actions now could bypass dirty-document or running-shell
negotiation. Experiment 009 owns that lifecycle work.

The final command/contract/QtADS suite passes 50 cases with one intentional
stock-backend skip. Compilation and `git diff --check` pass. The implementation
commit is `5a70ab9`.

### Platform menu ownership

`MenuProjectionMode` separates `SHARED_NATIVE` from `PER_FRAME` ownership.
macOS selects one parentless, application-lifetime native `QMenuBar` and one
set of application-shortcut actions shared by every peer frame. The bar exists
before any frame, is never inserted into a QtADS layout, and remains alive when
tracked frames are destroyed. This follows Qt's documented mechanism for one
menu shared by all macOS windows and removes the hidden `QMainWindow` from menu
availability.

Windows and Linux select non-native menu bars parented to every peer frame,
with window-scoped actions and no shared application bar. Their height is
reserved with peer-window content margins rather than insertion into QtADS's
private floating-container layout. Tests
exercise `darwin`, `win32`, and `linux` policy selection; direct platform-style
and desktop-global-menu replay remains part of Experiment 010's portability
matrix.

The manual macOS pass closed peer windows and successfully invoked Quit from a
surviving frame. Real peer and legacy Pyzo smoke tests pass sequentially, and
the real peer smoke asserts parentless shared ownership on macOS versus
per-frame ownership elsewhere. The full command/contract/QtADS suite passes 51
cases with one intentional stock-backend skip; compilation and diff checks
pass. The coordinating implementation is `646fc4e`; the Pyzo assertion is
`dca017a`.

### Dynamic command synchronization

`CommandRegistry.states_for()` resolves one active context for an ordered
command set, preventing a focus transition from mixing states within one menu
refresh. Descriptors may provide context-dependent labels, enabled and checked
predicates, shortcuts, and explicit checkability. A menu provider may also
change command membership and order from that same context snapshot.

`QtAdsCommandProjector.refresh()` reconciles every native or per-frame action
from the snapshot. It runs when a menu opens, when QtADS reports focused-dock
changes, and on explicit application refresh. Unchanged actions retain identity;
removed actions are retired; new actions retain late-bound invocation through
the registry. Tests prove that a removed stale action cannot invoke a command
disabled in the new context.

The experiment exposed a QtADS ownership boundary: inserting application chrome
into a `CFloatingDockContainer` layout lets authoritative rerenders delete that
foreign layout item. Per-frame menu bars now remain host-level children and use
content margins to reserve space. Refresh prunes invalid Qt wrappers and
rediscovers the manager's current floating containers, covering container
replacement that does not provide a durable creation signal.

The full command/contract/QtADS suite passes 54 cases with one intentional
stock-backend skip. Peer and legacy Pyzo smoke tests, compilation, and diff
checks pass. The implementation commit is `85427d8`.
