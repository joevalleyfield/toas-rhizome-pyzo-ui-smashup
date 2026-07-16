# Experiment 009: Separate pane, frame, and application lifecycle

## Status

In progress. The clean-editor final/non-final view matrix is complete. Dirty
document save/discard/cancel negotiation is the currently claimed slice; shell,
frame, and application lifecycle states remain queued in the execution
checklist.

## Objective

Prove that document and interpreter lifecycle remains correct when panes and
peer frames are closed, moved, or restored through the docking backend.

## Dependencies

- Experiment 006 defines close negotiation and state transitions.
- Experiment 007 provides the backend behavior under frame closure.
- Experiment 008 may supply real Pyzo panes; a model pane may be used first.

## Acceptance criteria

- Closing a non-final editor view leaves its document alive.
- Closing the final dirty editor view supports save, discard, and cancel.
- Closing a frame containing multiple dirty documents is transactional: a veto
  or cancellation does not leave an accidental partial close.
- A dead shell can close directly.
- A running shell refuses closure or requires explicit confirmation; moving or
  regrouping it never implies interpreter termination.
- Closing the first-created frame behaves like closing any other frame and does
  not inherently quit the application.
- Empty-frame behavior and application-shutdown policy are explicit and tested
  separately.
- Backend widget hiding or destruction cannot bypass application lifecycle
  policy.

## Allowed write surface

- Peer-frame contract and lifecycle implementation/tests.
- The local Pyzo project surface needed for document and shell policy.
- Root-level experiment notes and this task artifact.

## Completion evidence

Record a state matrix covering clean/dirty documents, final/non-final views,
dead/running shells, single/multiple panes, and frame/application closure.
Include automated results and any backend event paths that required interception.

## Progress evidence

### Clean editor and shared-document views

The close-policy contract now receives an immutable `CloseRequest` containing
the complete pane set and reason for the transaction. A policy can therefore
distinguish closing one of several views from closing every view in a group or
frame; it does not infer finality independently for each pane.

`DocumentViewRegistry` owns document-to-view membership independently from
workspace placement. Its close policy proves these states:

- closing a non-final view removes only that pane and leaves the document alive;
- closing the final clean view closes the document exactly once without setting
  application shutdown;
- a transaction closing all views closes once, while a transaction closing a
  subset preserves the document;
- dirty final-view and pinned-view closure are refused until their explicit
  negotiation slices are installed;
- tabbing and floating do not invoke lifecycle callbacks;
- stale duplicate closure and failed binding rollback are idempotent.

Real Pyzo peer editors now route ordinary `closeFile()` through workspace close
negotiation. The committed document callback uses a separate internal removal
path, so removing the editor host cannot recursively request closure after the
workspace has already committed. Peer mode permits the final editor group to
disappear; opening a new file recreates a document pane without treating the
operation as application Quit.

Stored Pyzo editor state still uses the legacy nested-tab representation. Its
conversion is now an explicit startup migration phase: lifecycle binding is
suspended only around `restoreEditorState()`, the manager distributes restored
items into independent hosts, and completion requires every settled peer host
to contain at most one document before bindings are reconciled. Normal runtime
binding retains the strict one-document-per-editor-pane invariant. Each
`FileItem` carries an immutable lifecycle serial so document identity survives
Qt tab-data wrapper conversion and Save As naming changes.

The real-Pyzo smoke closes one of two clean editors, closes the final editor,
asserts that shell panes and application lifetime remain intact, creates a new
editor, and verifies command/status projection IDs converge with live frame
IDs after deferred deletion.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 73 peer-frame tests passed with three intentional capability skips;
- the real peer-mode Pyzo smoke passed clean editor lifecycle, pane movement,
  debugger routing, native overlays, independent shells, and clean shutdown
  without uncaught exceptions;
- the legacy Pyzo layout control remained green;
- Python compilation and root/Pyzo `git diff --check` passed.
