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

Before creating the ADS manager, the Pyzo integration enables
`DragPreviewIsDynamic`, `DragPreviewShowsContentPixmap`,
`DragPreviewHasWindowFrame`, `FocusHighlighting`, and
`EqualSplitOnInsertion`. These are exposed by the published PySide6QtAds
binding through `CDockManager.eConfigFlag`. Pyzo's source smoke test still
passes with the flags enabled.

The five-point `CDockOverlayCross` is created by QtADS automatically during a
drag, but its overlay windows can sit behind the drag preview on macOS. The
Pyzo integration now applies `WindowStaysOnTopHint` to both ADS overlay windows
as a narrow application-side stacking hook. The source smoke test passes with
this hook. The five-point cross remains absent in the current macOS interactive
build and is explicitly deferred as a separate QtADS/macOS investigation; it
does not block the current editor-group integration work.

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
