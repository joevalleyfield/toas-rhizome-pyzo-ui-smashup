# Experiment 002: Prove the docking mechanism independently

## Objective

Demonstrate that QtADS or a functionally equivalent framework can provide the
required Visual Studio-like layout interactions with the Qt stack used by Pyzo.

## Acceptance criteria

- Multiple editor-like widgets can coexist in separate groups.
- Groups support horizontal and vertical nested splits.
- Groups or panes can float, move by drag-and-drop, and re-dock.
- The interaction works on macOS and does not depend on a platform-specific
  design that obviously blocks Windows or Linux.
- The binding/build decision and any compatibility gap with Pyzo are recorded.

## Allowed write surface

- A dedicated root-level spike directory.
- Dependency build/configuration files only when necessary for the experiment.
- This task artifact for evidence.

## Completion evidence

Record the runnable entry point, dependency revisions, screenshots or a concise
interaction log, and compatibility findings.

## Progress evidence

### Runnable slice

Added `spikes/qtads_layout/main.py` with a PySide6/QtADS layout demo and a
companion README. The demo creates six dock widgets representing editor groups,
an editor tab, shell, and file browser. It creates multiple dock areas,
serializes/restores the layout, and supports an interactive mode for manual
drag, float, and re-dock testing.

Smoke command from the repository root:

```sh
UV_CACHE_DIR=/tmp/pyzo-uv-cache \
QT_QPA_PLATFORM=offscreen \
uv run --python 3.12 --with PySide6-QtAds \
  python spikes/qtads_layout/main.py --test
```

Result: passed with six dock widgets and six visible dock areas. The Qt
offscreen plugin emits only its expected font and `propagateSizeHints()`
warnings.

### Compatibility finding

The published PySide6 binding installs as `PySide6QtAds`, not
`PySide6.QtAds`. Its API uses Python signatures such as
`addDockWidgetTab(DockWidgetArea, DockWidget)`. Pyzo's existing Qt abstraction
can select PySide6, so a PySide6 integration path exists without forcing PyQt5.

The published binding exposes stable semantic hooks for the important layout
transitions: `CDockWidget.setFloating()`, `CDockManager.addDockWidget(...)`,
`addDockWidgetTabToArea(...)`, and `saveState()`/`restoreState(...)`. The smoke
test now uses `setFloating()` followed by `addDockWidget(...)` to prove a
float/re-dock cycle deterministically. A direct `addDockWidgetFloating(...)`
attempt was not used because it leaves an offscreen floating window alive in the
headless harness; the semantic widget hook avoids that harness issue.

Actual mouse-driven drag choreography remains a separate UI-level check. It is
not necessary for deterministic Pyzo integration tests when the semantic hooks
can express the same state transition.

### Current status

This is a meaningful partial result, not completion of the full task. The
independent binding and layout construction are proven; manual macOS behavior
and Pyzo integration remain open.

## Final status

The macOS interactive check was completed: drag-and-drop rearrangement is
working as expected, including the intended QtADS layout behavior. Combined
with the automated construction, float/re-dock, tab, and state round-trip smoke
coverage above, the independent docking spike is complete.
