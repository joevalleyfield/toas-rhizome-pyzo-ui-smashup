# Experiment 004: Preserve Pyzo tools and post-mortem debugging

## Status

In progress. Ordinary run, live debugging, post-mortem re-entry, and explicit
captured-frame source navigation are verified. Live execution against the
selected captured frame is claimed next.

## Objective

Verify and repair the core Pyzo workflows in the multi-editor layout, with
special emphasis on post-mortem re-entry and frame-local live execution.

## Dependencies

- Experiment 008 projects the required Pyzo surfaces through the peer-frame
  contract.
- Experiment 009 prevents placement and frame closure from bypassing document
  or interpreter lifecycle.

## Acceptance criteria

- Editor, shell, file browser, run workflow, and live debugging remain usable.
- An unhandled exception enters a post-mortem debugging session.
- A captured stack frame can be selected and its source opened in an
  application-selected editor pane without assuming a privileged frame.
- Live interpreter code executes against the selected captured frame.
- With multiple eligible kernels, editor-originated Run and Debug commands
  visibly identify a remembered target or require an explicit choice; pane
  focus alone never silently changes execution affinity.
- Moving a shell between workspace contexts preserves its kernel cwd and
  interpreter identity unless an explicit command changes them.
- The workflow remains valid after splitting, floating, moving between peer
  frames, and re-docking editor panes.
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

## Progress evidence

### Ordinary run and live debugging

The real peer-mode smoke now waits for the recreated default shell's kernel to
be ready and drives the application Run menu against a temporary source file.
Ordinary execution is verified through the kernel introspection channel before
the same editor installs a real breakpoint and runs again.

The live-debug transition proves:

- the active shell enters debug mode 2 at the expected file and line;
- the selected source remains the application-selected editor pane;
- the editor's current-line indicator and the shell host's stack projection
  agree with kernel debug state;
- selected-frame local evaluation returns the value visible before the
  breakpoint line executes;
- Continue leaves debug mode and produces the expected final result; and
- breakpoint and temporary-document cleanup complete through normal
  application lifecycle paths.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- the extended real peer-mode smoke completed the run/debug state machine in
  1.9 seconds and the full application smoke shut down cleanly;
- all 147 peer-frame tests passed with three intentional capability skips;
- the legacy Pyzo ADS/editor/debugger/shell control shut down cleanly; and
- Python compilation and root/Pyzo `git diff --check` passed.

### Captured-frame selection and source navigation

Before raising the post-mortem exception, the smoke floats its source editor
into a new named peer frame. After re-entry selects the innermost raising
frame, it sends `DB FRAME` for the captured outer function and waits for the
kernel's selected-frame index to change.

The outer frame resolves to its call site at line 6, updates the debug-line
indicator in the same floated editor, and leaves that editor hosted by the
named peer frame. No hidden main-window editor, central widget, or first-created
frame participates in source lookup or selection.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- the expanded real peer-mode state machine completed frame selection and
  source navigation in 4.1 seconds before clean shutdown;
- all 147 peer-frame tests passed with three intentional capability skips;
- Python compilation and root/Pyzo `git diff --check` passed.

### Post-mortem re-entry

The real-kernel state machine now follows live debugging with a second source
file containing nested calls and an unhandled `RuntimeError`. It waits until
the kernel records that exception, issues Pyzo's `DB START` command, and
verifies post-mortem debug mode 1 rather than inferring success from traceback
text.

The captured innermost frame resolves to the raising file and line in the
application-selected editor pane. Its debug indicator matches kernel state,
and introspection reads the captured local value `84` before `DB STOP` returns
the shell to ordinary mode and lifecycle cleanup removes the temporary pane.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- the real peer-mode run/live-debug/post-mortem state machine completed in 3.5
  seconds and application shutdown remained clean;
- all 147 peer-frame tests passed with three intentional capability skips;
- Python compilation and root/Pyzo `git diff --check` passed.
