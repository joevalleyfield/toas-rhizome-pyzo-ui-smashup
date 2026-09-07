# Task 018 local retention evidence

Date: 2026-09-07

## Probe delivered

Added an isolated `QtDocumentRetentionProbe` that constructs actual
`PyzoEditor` widgets and binds two views to one `DocumentResourceRegistry`
document. The probe covers shared text projection, independent selections,
native edit projection, paste, deletion, multiline indentation, notification
capture, JSON-compatible serialization, destruction, and fresh-widget
recreation. It uses public editor APIs and does not inspect Qt's private undo
stack or modify Pyzo production code.

The correction pass now gives the probe an isolated temporary Pyzo config and
the small set of application services that `PyzoEditor` expects. Recreation
binds fresh widgets to views already restored by the registry; it does not
register their identities again. Text projection blocks signals, disables
native widget history, and restores the target cursor anchor/position. Undo
and redo route through the registry history and re-project every live view.

The added regression test edits one view, serializes the registry, destroys
the widgets, recreates fresh widgets, then undoes and redoes through the other
view. This demonstrates that the registry, rather than a widget's native
history, is authoritative across widget lifetimes.

## Verification

The real Qt probe runs successfully with the project-local `uv` shim and the
offscreen platform:

```text
PYTHONPATH=deps/pyzo:. QT_QPA_PLATFORM=offscreen \
  .codex-local/bin/uvt run --python 3.12 --with PySide6 --with ipython \
  python -m unittest discover -s spikes/peer_frames \
  -p 'test_qt_document_retention_probe.py' -v
```

Result: **4 tests passed**.

The technology-neutral document-resource regression suite also passes:

```text
PYTHONPATH=deps/pyzo:. .codex-local/bin/uvt run --python 3.12 \
  python -m unittest spikes.peer_frames.test_document_resources -v
```

Result: **19 tests passed**. `git diff --check` and Python 3.12 compilation
also pass. No source file writes occur during the probe.

## Stop-boundary result

The implementation remains a prototype probe. No Pyzo production editor code
was changed, and 019 remains gated pending Astra's acceptance of the
adapter conclusion. The probe uses a test-owned fixture for Pyzo globals and
does not exercise a full application controller or real menu bar.

## Review question

Astra should review the corrected probe and decide whether the isolated
real-editor evidence is sufficient to accept 018. Task 019 must remain gated
until that review accepts the real-editor undo/history behavior.
