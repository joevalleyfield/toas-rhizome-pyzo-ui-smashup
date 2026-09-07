# Pyzo Docking Workbench Requirements

For the current local-workspace product, the
[2026-09-06 scope amendment](docs/local-workspace-scope-2026-09-06.md) takes
precedence over conflicting original prototype requirements below, especially
final-view closure and application-only recovery. Closing retains editing state;
Save and Discard are explicit document operations. Original prototype acceptance
is historical evidence and does not establish continuous-retention acceptance.

## Purpose

Explore whether Pyzo can contribute the foundation for a more capable Python
development workbench, using Qt Advanced Docking System (QtADS) or a
functionally equivalent framework as an initial docking prototype. The first
prototype focuses on removing Pyzo's single-editor-area limitation while
preserving its debugging workflow. Neither Pyzo's current window ownership nor
QtADS's container hierarchy defines the eventual product architecture.

## Application topology

The application owns workspace topology, documents, shells, commands, and
debugger state. Every user-visible workspace frame is a peer; there is no
privileged main workspace window.

- Any editor, shell, or tool pane can be the first pane in any frame.
- Panes can move and regroup without transferring ownership of their document,
  interpreter, or debugger state to a frame.
- Closing one particular frame does not inherently quit the application.
- Menus, status, focus, and commands follow active context without making the
  active frame the application owner.
- Backend-specific roots, managers, and hidden widgets remain private
  implementation details and cannot impose user-visible placement or lifecycle
  asymmetry.
- Closing the final frame follows platform application conventions. On macOS
  and other platforms with a usable application-level handle independent of
  windows, the application may remain alive with zero frames. Where no such
  handle exists, final-frame closure is application Quit; the process must not
  remain alive only through a hidden window or tray workaround.
- Activating a surviving zero-frame application recreates one ordinary peer
  frame from the configured default template. The factory fallback resembles
  legacy Pyzo's editor, shell, and standard tools with peer behavior enabled.
  An unreadable configured template is logged before fallback; individual pane
  failures remain pane-owned error/loading states. If no pane can be created,
  report the fatal error visibly where possible and exit with status 1.

The complete model and its lifecycle implications are recorded in
[Application Topology](docs/application-topology.md).

## First prototype

The prototype begins as a locally modified Pyzo based on the latest HEAD from
Pyzo's canonical published source. Substantial source changes or local forks of
Pyzo and QtADS are acceptable, as is replacing QtADS if its architecture cannot
support the required user model. Upstream compatibility is desirable, but is
not an initial priority.

The prototype must provide Visual Studio-like layout management:

- Multiple editor groups visible at the same time.
- Multiple document tabs within each editor group.
- Horizontal and vertical nested splits.
- Floating editor groups and panes.
- Drag-and-drop rearrangement and re-docking.
- Peer workspace frames with no user-visible main-frame distinction.

## Pane lifecycle requirements

Document and interpreter lifecycle must be independent of docking lifecycle.

- Dirty state belongs to the document/editor, or to a shared buffer when
  multiple views show one document; it does not belong to a frame.
- Closing the final view of a dirty document must offer save, discard, and
  cancel behavior.
- Closing a frame must not silently discard dirty documents.
- Application exit automatically uses a retained-dirty session disposition by
  default, distinct from save or discard. The application durably snapshots
  every affected named or untitled buffer and restores its content, dirty
  marker, and text metadata on the next launch. Snapshot failure blocks exit
  and offers Retry, Save affected, Discard affected and exit, or Cancel. This
  is a session-lifecycle operation, not an implicit consequence of closing an
  individual pane or frame.
- A dead shell may close directly.
- Closing any live shell, including an idle, starting, executing, or debugging
  interpreter, must be refused or explicitly confirmed while kernel detachment
  is unavailable. Confirmation means terminate-and-close; debugging warnings
  must identify the loss of the active stack state.
- Moving or regrouping a shell must never imply interpreter termination.
- Detachable/reconnectable kernels and multiple editor views over one buffer
  are future-compatible design allowances, not first-prototype requirements.

## Pyzo capabilities to preserve

The following native Pyzo workflows must remain usable alongside the new layout
system:

- Editor
- Shell
- File browser pane
- Running code
- Live debugging
- Post-mortem debugging

Post-mortem debugging is a hard requirement. The prototype must support entry
into a post-mortem debugging session after an unhandled exception, navigation
to a captured stack frame, and live interpreter execution against that selected
frame.

## Acceptance workflow

The prototype is viable if it can demonstrate this complete workflow:

1. Open multiple source documents.
2. Arrange them across multiple split editor groups.
3. Float, move, and re-dock editor groups.
4. Run code that raises an unhandled exception.
5. Enter post-mortem debugging.
6. Select a captured stack frame.
7. Execute live code in the interpreter against that frame.
8. Continue using the editor, shell, file browser, and run/debug workflows
   without losing state.

## Platform expectations

Development and initial validation will happen on macOS. The architecture must
remain practical to port to Windows and Linux, and should avoid platform-
specific choices that would make those ports difficult.

Zero-frame survival and activation-driven default-frame creation are fixed
platform policy in the first prototype. User preferences for either behavior
are follow-on configuration work and cannot enable an unreachable background
process on a platform without an independent application handle.

## Deferred scope

The first prototype does not include:

- A toas transcript-editor window type in Pyzo.
- Broader rhizome integration.

Those integrations remain candidate follow-up work after the Pyzo and docking
feasibility question has been answered.

## Important edge cases

- Moving or floating editors during an active debugging session.
- Preserving breakpoints, traceback navigation, shell state, and debugger
  context across layout changes.
- Executing code against the correct captured stack frame.
- Re-docking panes without losing documents or session state.
- Opening traceback locations in the correct editor group.
- Maintaining portability across Qt-supported desktop platforms.

## Feasibility deliverable

Alongside the runnable prototype, record whether Pyzo is a viable foundation for
later toas/rhizome integration, including any architectural limitations,
necessary local fork points, and portability risks discovered during the work.
