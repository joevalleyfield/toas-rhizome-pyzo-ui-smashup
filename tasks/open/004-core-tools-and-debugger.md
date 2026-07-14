# Experiment 004: Preserve Pyzo tools and post-mortem debugging

## Objective

Verify and repair the core Pyzo workflows in the multi-editor layout, with
special emphasis on post-mortem re-entry and frame-local live execution.

## Acceptance criteria

- Editor, shell, file browser, run workflow, and live debugging remain usable.
- An unhandled exception enters a post-mortem debugging session.
- A captured stack frame can be selected and its source opened in the correct
  editor group.
- Live interpreter code executes against the selected captured frame.
- The workflow remains valid after splitting, floating, moving, and re-docking
  editor groups.
- Breakpoints, traceback navigation, shell state, and debugger context are not
  silently lost.

## Allowed write surface

- The local Pyzo project surface under `deps/pyzo` or its explicitly chosen
  fork/worktree.
- Root-level integration notes and reproducible fixtures.
- This task artifact for evidence.

## Completion evidence

Record the end-to-end procedure, observed state transitions, failures, fixes,
and any unresolved debugger limitations.
