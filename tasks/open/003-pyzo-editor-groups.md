# Experiment 003: Introduce multiple editor groups in Pyzo

## Objective

Make the smallest Pyzo-local change that supports multiple simultaneously
visible editor groups while retaining document tabs and ordinary editing.

## Acceptance criteria

- Two or more editor groups are visible simultaneously.
- Documents can be opened and moved between groups without losing content.
- Nested splits, floating groups, drag-and-drop, and re-docking work.
- Existing editor operations and document-tab behavior remain usable.
- The change is attributable to a clear Pyzo fork or integration boundary.

## Allowed write surface

- The local Pyzo project surface under `deps/pyzo` or its explicitly chosen
  fork/worktree.
- Root-level integration notes.
- This task artifact for evidence.

## Completion evidence

Record the changed Pyzo components, demonstration procedure, known limitations,
and whether the change required a fork rather than extension points.

## Progress evidence

### Central ADS integration

`deps/pyzo/pyzo/core/main.py` now creates a `PySide6QtAds.CDockManager` and
hosts Pyzo's existing `EditorTabs` widget in a central `CDockWidget`. Pyzo's
source smoke test passes with this integration and the existing shell, tools,
startup, and shutdown path intact.

### Two editor groups

The same main window now creates a second `EditorTabs` widget in a right-side
ADS editor dock. Both groups are visible simultaneously, each has its own
document tabs, and the smoke test creates an initial document in each group.

`deps/pyzo/pyzo/core/editorGroups.py` adds an `EditorGroupManager` facade that
preserves the existing `pyzo.editors` service shape. Active-group operations
delegate to the focused editor group; iteration and bulk operations span all
groups. ADS focus changes select the active group.

### Verification

From `deps/pyzo`:

```sh
UV_CACHE_DIR=/tmp/pyzo-uv-cache \
PYTHONPATH=. \
QT_QPA_PLATFORM=offscreen \
PYZO_LOG=/tmp/pyzo-ads-groups.log \
uv run --python 3.12 --with PySide6-QtAds --with ipython \
  python pyzolauncher.py --test
```

Result: passed on macOS with Pyzo `4.21.0`, CPython `3.12.13`, and PySide6
`6.11.1`. No QtADS integration source was modified; the Pyzo checkout is the
local fork surface.

### Known limitations

- The current user-facing command moves the active document cyclically to the
  next editor area; choosing an arbitrary named target and creating/removing
  groups remain future work.
- Some Pyzo integrations still assume a single active group and need explicit
  interactive validation, especially breakpoint editing and less-traveled
  tool workflows.
- The second group is currently created as part of startup rather than through
  a user-facing “New editor group” action.

The routing facade and ADS focus integration now also pass the source smoke test
after explicit group registration. The remaining hard problem is document
ownership: `FileTabWidget.removeTab()` intentionally destroys the editor, so
moving an existing document between groups requires a dedicated detach/attach
operation rather than reusing the current close path.

### Docking feedback configuration

The Pyzo integration now leaves QtADS drag-preview and overlay configuration at
the library defaults, matching the standalone spike. It enables only
`EqualSplitOnInsertion` for predictable editor-area sizing. This removes the
speculative overlay window-stacking and dynamic-preview hooks; the five-point
`CDockOverlayCross` discrepancy remains an open interactive macOS issue for
the next investigation.

### Unified dock-container slice

The shell now uses an ADS `CDockWidget`, and `ToolDockWidget` selects an ADS
backing container when Pyzo is running with PySide6QtAds while retaining the
original `QDockWidget` fallback. Tool placement and split placement route
through the ADS manager in the integration mode. The Pyzo source smoke test
passes, and normal startup initialization confirms the tool adapter's base is
`CDockWidget`.

The remaining validation is functional loading and interaction with the file
browser and other tools in the interactive macOS session.

### Document move slice

`EditorTabs.detachCurrentItem()` now removes a tab through the base
`QTabWidget` API without destroying its `FileItem` or editor. `attachItem()`
adds that same item to another group, and `EditorGroupManager` exposes
`moveCurrentEditorToGroup()` while preserving active-group routing.

The Pyzo source smoke test now performs a move-to-primary/move-to-secondary
round trip and asserts that the same editor object survives. It reports
`Pyzo editor-group move smoke test passed` before the normal startup timer.

The View menu now exposes “Move editor to next area,” backed by the manager's
cyclic target-group operation. The smoke test also loads the current source
file through the active secondary group, verifies ownership, broadcasts a
debug-line indicator to all groups, and reports
`Pyzo debugger editor-group routing smoke test passed`.

The remaining product-level work is arbitrary target selection, group
lifecycle, and interactive validation of the remaining tools across groups.

The source smoke test now also loads and closes the file-browser tool through
`ToolManager`, asserting that its container is an ADS `CDockWidget`. It reports
`Pyzo ADS tool-container smoke test passed`.

### Dual-layer docking guide

The native macOS `CDockOverlayCross` windows are created, positioned, and
shown by QtADS during a drag, but their indicator pixmaps do not composite in
the Pyzo-hosted layout. An application-owned, mouse-transparent guide now
renders QtADS's existing drop state without replacing its docking behavior.

The guide displays blue inner targets for tab/local-area splits and amber
double-arrow outer targets for whole-container edge splits. It stabilizes the
rapid container-overlay/dock-area-overlay event sequence by polling current
visibility. Its rectangles now mirror QtADS's native hit geometry: a tight
45-pixel inner cross and outer targets directly on the container edges. The
source smoke test asserts painted inner pixels and the amber outer accent and reports
`Pyzo ADS dual-layer drop-guide paint smoke test passed`.

### Independent document and shell docks

The nested-selector prototype has been replaced with document- and
interpreter-level ADS ownership. Every open document is held by a one-document
`EditorTabs` host whose legacy tab bar is hidden; every interpreter is held by
a one-shell `ShellStackWidget`. QtADS is therefore the only visible tabbing and
splitting layer, and either kind of window can be dragged, split, floated, or
tabbed independently.

`EditorGroupManager` now creates a host for each new or loaded document,
searches all hosts before opening a duplicate, aggregates breakpoints and
persistence across hosts, and removes an empty host when its document closes.
`ShellGroupManager` similarly preserves the global `pyzo.shells` service while
routing focus, debug state, post-mortem controls, and shell closure across
independent hosts. The one-document/one-shell legacy widgets deliberately keep
Pyzo's existing find, debug-stack, and interpreter toolbar implementations.

The full offscreen source test ran outside the filesystem/network sandbox so
two real shell brokers could bind local ports. It passed and reported:

- `Pyzo independent editor-dock smoke test passed`
- `Pyzo debugger document-dock routing smoke test passed`
- `Pyzo independent shell-dock smoke test passed`

The test also closes one document and one live shell and verifies that their
ADS hosts are removed and focus returns to a surviving host. Python compilation
and `git diff --check` pass. Ruff was unavailable in the offline dependency
cache, so lint verification remains to be run when that tool is available.
