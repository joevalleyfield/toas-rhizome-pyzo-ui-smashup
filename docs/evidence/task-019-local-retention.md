# Task 019 local retention evidence

## Current state

019 remains **IN_PROGRESS**. The approved 018 adapter is wired into the live
peer editor lifecycle at Pyzo revision `3c8f7be7`; the root progress note is
at `03ff7cfc`.

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

## Remaining acceptance

- Run and record a fresh-process round-trip that restores live editor text,
  authoritative undo history, cursor/view state, and parser provenance.
- Confirm duplicate named-file opens resolve to one retained document through
  that fresh-process harness.
- Full GUI acceptance remains unrun; offscreen smoke is the current evidence.
