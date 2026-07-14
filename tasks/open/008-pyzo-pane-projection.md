# Experiment 008: Project Pyzo surfaces as application-owned panes

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

## Allowed write surface

- The local Pyzo project surface under `deps/pyzo` or its chosen fork/worktree.
- The peer-frame adapter and integration tests.
- Root-level integration notes and this task artifact.

## Completion evidence

Record the Pyzo ownership assumptions removed or wrapped, the demonstrated pane
matrix, verification commands, and any remaining main-window dependencies.

