# QtADS layout spike

This is the first independent docking experiment. It intentionally uses
editor-like `QPlainTextEdit` widgets rather than Pyzo components so the docking
framework can be evaluated before Pyzo is modified.

## Run the smoke test

From the repository root:

```sh
UV_CACHE_DIR=/tmp/pyzo-uv-cache \
QT_QPA_PLATFORM=offscreen \
uv run --python 3.12 --with PySide6-QtAds \
  python spikes/qtads_layout/main.py --test
```

The smoke test constructs six dock widgets, creates multiple dock areas and an
editor tab group, programmatically floats and re-docks an editor, serializes/
restores the layout, and exits. It does not prove mouse choreography.

## Run the interactive demo

```sh
UV_CACHE_DIR=/tmp/pyzo-uv-cache \
uv run --python 3.12 --with PySide6-QtAds \
  python spikes/qtads_layout/main.py
```

Manually verify that editor groups can be split, floated, dragged, tabbed, and
re-docked. The published binding is imported as `PySide6QtAds`, while Pyzo's
own Qt abstraction remains compatible with PySide6.

## Automation seam

The binding exposes semantic layout operations that are more stable than
simulated mouse coordinates:

- `CDockWidget.setFloating()` moves a dock into a floating container.
- `CDockManager.addDockWidget(...)` re-docks it into a selected area, including
  a target dock area for a split or tab insertion.
- `CDockManager.addDockWidgetTabToArea(...)` inserts a dock into an existing
  tab group.
- `CDockManager.saveState()` and `restoreState(...)` provide layout-state
  round-trip coverage.

These are the preferred seams for deterministic integration tests. A later UI
test can cover the visual drag gesture itself, but Pyzo integration should use
the semantic operations and assert the resulting layout state.
