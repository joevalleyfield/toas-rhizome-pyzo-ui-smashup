# Experiment 008: Project Pyzo surfaces as application-owned panes

## Status

In progress. The first real-Pyzo peer-frame projection and native-overlay slice
is complete; application chrome and deeper run/debug validation remain.

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

- Menus, status, and commands still live on the hidden Pyzo `QMainWindow`; they
  are not yet projected into every peer frame.
- Run/debug and post-mortem behavior retains the existing service wiring but
  still needs end-to-end interactive validation through peer-frame moves.
- Tool close buttons are conservatively disabled in peer mode until Experiment
  009 supplies application-level close negotiation.
