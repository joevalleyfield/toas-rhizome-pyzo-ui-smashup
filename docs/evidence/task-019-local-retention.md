# Task 019 local retention evidence

## Current state

019 is **COMPLETE**. Final Pyzo revision: `bdb55074`; root completion evidence
is recorded in this revision.

## Verified behavior

- Peer editor binding assigns document/view identities and publishes edits to
  the application-owned resource registry.
- Shared peer views, parser notification, Undo/Redo routing, save-baseline
  adoption, and owner-scoped teardown are wired through the adapter.
- Startup and persistence smoke runs use temporary config/data/tools and
  recovery directories, with command-server startup stubbed before Pyzo
  import; user preferences and iCloud-backed state are not read or changed.
- The isolated real-app smoke reaches peer workspace session round-trip, pane
  movement, clean and dirty editor lifecycle checks, and zero-frame survival.
- Binding preserves the editor's initial dirty state across delayed native
  editor setup notifications.

## Commands and results

- `PYTHONPATH=deps/pyzo:. .codex-local/bin/uvt run --python 3.12 --with PySide6 --with <pinned QtAds wheel> python -m unittest discover -s spikes/peer_frames -p 'test_*.py' -q`
  - **248 tests passed; 1 skipped.**
- `PYTHONPATH=../..:. ../../.codex-local/bin/uvt run --python 3.12 --with PySide6 --with pytest pytest tests -q`
  - **15 tests passed.**
- Focused retention/Qt/persistence pytest matrix
  - **53 tests passed; 2 deprecation warnings.**
- Isolated offscreen real-Pyzo peer smoke with temporary application paths,
  recovery path, and pre-import command-server stub
  - peer binding, application controller, workspace persistence session,
    pane movement, clean/dirty close lifecycle, shell docks, and zero-frame
    smoke checks passed.
- A two-process recovery attempt wrote a fresh recovery generation in process
  one, but process two encountered an offscreen Qt teardown race while the
  existing smoke callback captured workspace geometry
  (`CFloatingDockContainer` was already deleted). This is not counted as
  fresh-process acceptance evidence.
- A clean two-process live-resource probe passed: process one performed real
  editor Save, edit, and Undo operations, and process two restored the saved
  document with exact text (`abc\\n`), revision `5`, undo `[""]`, redo
  `["abcd\\n"]`, path, and one associated persisted view. The second process
  also logged `workspace session restore failed: unregistered panes:
  ['editor-2']`; the resource/history restoration passed, but editor-pane
  recreation is not yet wired and remains a boundary for the later
  close/reopen slice.
- The persistent probe now recreates the actual saved editor in process two,
  restores its identity, text, clean state, cursor, and view record, and
  passes live Undo followed by Redo after restart. The layout no longer emits
  the earlier unregistered-editor-pane warning.
- The same probe now waits for the automatic 017 checkpoint instead of calling
  persistence Save explicitly. It passes Save → edit → Undo, persists the
  post-Undo state, and verifies live Undo/Redo after restart. Undo/Redo now
  refresh the pending checkpoint snapshot as well as the visible registry.
- Reopening the restored file by absolute path and `./saved.py` repeatedly
  reused the same editor, document identity, view identity, and history.

## Remaining acceptance

- Complete the fresh-process round-trip at the live-editor/pane layer; the
  application-owned resource, history, identity, and view-record restoration
  now pass.
- Connect live edits to the 017 `RetentionCoordinator` and prove automatic
  checkpoint scheduling without an explicit persistence Save call. **Passed**
  in the persistent two-process probe.
- Full GUI acceptance remains unrun; offscreen smoke is the current evidence.
