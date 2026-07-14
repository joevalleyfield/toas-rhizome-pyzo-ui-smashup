# Experiment 001: Establish the Pyzo baseline

## Objective

Run the assembled latest Pyzo checkout on macOS and record the current Qt
binding, editor/container architecture, run workflow, live debugging workflow,
and post-mortem debugging workflow.

## Acceptance criteria

- Pyzo's current launch/build path is recorded.
- The Qt binding and relevant dependency versions are recorded.
- The current single-editor-area behavior is demonstrated or documented from
  source.
- A reproducible baseline procedure exists for run, live debugging, and
  post-mortem debugging.
- Any baseline blocker is recorded with evidence.

## Allowed write surface

- `tasks/open/001-baseline-pyzo.md`
- Root-level investigation notes or compatibility notes.
- No source changes in dependency checkouts unless required to make the
  baseline runnable; such changes must be recorded explicitly.

## Completion evidence

Record commands, revision identifiers, observed behavior, and blockers.

## Completion evidence

### Revisions and runtime

- Pyzo checkout: `26c2c32778dddf8fca3c1a44112941b22f075264`
- Pyzo version: `4.21.0`
- Host: `macOS-26.5.2-arm64-arm-64bit`
- Runtime used for the smoke test: CPython `3.12.13`
- Qt binding: PySide6 `6.11.1`
- IPython: `9.15.0`
- Pyzo's Qt selector supports PySide6, PyQt6, PySide2, and PyQt5, in that
  preference order when no `QT_API` override is supplied.

### Launch procedure

From `deps/pyzo`:

```sh
UV_CACHE_DIR=/tmp/pyzo-uv-cache \
PYTHONPATH=. \
QT_QPA_PLATFORM=offscreen \
PYZO_LOG=/tmp/pyzo-baseline.log \
uv run --python 3.12 --with PySide6 --with ipython \
  python pyzolauncher.py --test
```

Result: passed. The built-in source test initialized the application, loaded
the themes, started and stopped the command server, ran for just over five
seconds, and exited with status 0. The offscreen Qt plugin emitted only the
expected `propagateSizeHints()` warnings.

The system Python 3.9.6 had no Qt wrapper installed, so a temporary uv runtime
was necessary. No Pyzo source files were modified for the test.

### Current UI architecture

- `pyzo/core/main.py` constructs one `EditorTabs` instance and installs it as
  the `QMainWindow` central widget.
- The same main window creates a shell `QDockWidget` and uses ordinary Qt
  nested/tabbed dock options for tools.
- `pyzo/core/editorTabs.py` owns one `FileTabWidget` containing the open
  documents and one find/replace widget.
- This confirms the current limitation is a single `EditorTabs` central widget,
  not a lack of tabs within that widget.

### Debugging procedure

The current kernel supports the required post-mortem workflow through its
debugger commands:

1. Run a file that raises an unhandled exception.
2. In the shell, enter `db start` to begin post-mortem debugging from the last
   traceback.
3. Enter `db frame N` to select a captured stack frame.
4. Execute an expression in the interpreter; the debugger switches the shell's
   active locals and globals to the selected frame before evaluation.
5. Use `db stop` to leave the debugging session.

The implementation evidence is in `pyzokernel/debug.py` (`do_start` and
`do_frame`) and `pyzokernel/interpreter.py` (frame-local `locals`/`globals`
handling). The GUI exposes the corresponding post-mortem action as
“Postmortem: debug from last traceback” and displays frame state through the
debug status channel.

### Baseline conclusion

The current Pyzo checkout is runnable and its core debugging architecture
already represents post-mortem state independently of the editor container.
The next experiment should test whether a docking prototype can replace or
wrap the single `EditorTabs` central widget without breaking the existing
shell/debug status pathways.
