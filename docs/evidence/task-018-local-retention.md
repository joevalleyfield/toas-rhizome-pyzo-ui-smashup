# Task 018 local retention evidence

Date: 2026-09-07

## Probe delivered

Added an isolated `QtDocumentRetentionProbe` that constructs actual
`PyzoEditor` widgets and binds two views to one `DocumentResourceRegistry`
document. The probe covers shared text projection, independent selections,
native edit/undo/redo, paste, deletion, multiline indentation, notification
capture, JSON-compatible serialization, destruction, and fresh-widget
recreation. It uses public editor APIs and does not inspect Qt's private undo
stack or modify Pyzo production code.

## Stop-boundary result

The real Qt tests could not start on this host. A basic `QPlainTextEdit` and
the PyzoEditor probe fail before widget construction because Qt reports the
bundled `offscreen`, `minimal`, and native `cocoa` platform plugins as
unavailable. The plugin binaries are present, but platform initialization
exits before the test body. This is an environment/runtime blocker, not a
probe assertion result.

Commands attempted:

```text
QT_QPA_PLATFORM=offscreen ... -m unittest spikes.peer_frames.test_qt_document_retention_probe -v
QT_QPA_PLATFORM=cocoa ... -m unittest spikes.peer_frames.test_qt_document_retention_probe -v
```

Both failed during Qt platform initialization. Static compilation and
`git diff --check` passed. The non-Qt retention/persistence/recovery/document/
lifecycle suite passed **106 tests**.

## Review question

Please provide a host/runtime with a loadable Qt platform plugin, or confirm
that this isolated probe is sufficient for a later real-editor acceptance run.
Task 019 must remain gated until real-editor undo/history behavior is observed
and accepted.
