# Experiment 011: Choose a tab edge for each group

## Status

In progress. The technology-neutral state and adapter-metadata slice is
complete. A source-built QtADS/PySide6 fork now renders all four per-group tab
positions. Interactive visual review, broader docking replay, portability, and
the Pyzo-facing group command remain.

## Objective

Allow every application tab group to independently place its tabs on the top,
bottom, left, or right, preserving Pyzo's useful editor/tool distinction while
making placement a user-controlled and persistent layout property.

## Dependencies

- Experiment 006 supplies application-owned group identity and serialization.
- Experiment 007 supplies the stock-QtADS peer-frame adapter and native docking
  interaction baseline.
- The first Experiment 008 slice supplies real editor, shell, and tool panes for
  final integration validation.

## Current technology evidence

Stock QtADS exposes only the global `CDockManager::TabsAtBottom` configuration
flag. `CDockAreaWidget` and `CDockAreaTitleBar` use that flag while constructing
their layouts, so even top versus bottom is not independently configurable by
dock area.

Left and right placement require a deeper change. `CDockAreaTabBar` constructs
a `QBoxLayout` in `LeftToRight` mode and uses x coordinates and widths for tab
hit testing, insertion, overflow, and movement. `CDockWidgetTab` similarly uses
horizontal drag bounds and vertical distance as the undock threshold. Dock-area
minimum-size and title-bar logic also assume horizontal tabs.

## Application semantics

- Tab side belongs to a stable group identity, not to a frame, pane, or global
  docking-manager setting.
- New editor groups default to top; new shell and tool groups default to bottom,
  preserving the useful distinction from stock Pyzo.
- A user override remains stable if the group's pane composition later changes.
- A center/tab merge uses the destination group's side because the incoming
  groups are flattened into that terminal tab group.
- An edge drop preserves each surviving group's side because their layout
  structure remains distinct.
- A newly split group inherits the source group's side unless the user changes
  it.
- Saving and restoring application layout preserves every group's selected side
  without exposing backend-specific values.

## Acceptance criteria

- The application contract represents `top`, `bottom`, `left`, and `right` on
  each group and rejects unknown values atomically.
- A user-facing group command can switch among all four sides without moving,
  recreating, or losing panes.
- Different groups in the same frame can use different sides simultaneously.
- All four placements render correctly with one tab, multiple tabs, long or
  elided titles, icons, close controls, and title-bar actions.
- Tab selection, reordering, center insertion, drag-to-float, and re-docking
  work in both horizontal and vertical orientations.
- Left/right tabs have an explicitly chosen readable label treatment; the spike
  compares rotated labels with horizontal labels in a vertical rail and records
  the decision.
- Native QtADS docking overlays remain unchanged and visible for every side.
- Center merges, edge merges, splits, floating, and reverse synchronization obey
  the application semantics above.
- Application-format save/restore round-trips mixed tab sides.
- Real Pyzo editor, shell, and tool groups receive the expected defaults and can
  be overridden independently.
- Keyboard focus, accessibility names, minimum sizing, high-DPI rendering, and
  macOS behavior are verified; Windows and Linux obligations are recorded.

## Experiment slices

1. Extend the technology-neutral group model, serialization, fake backend, and
   state-transition tests with a tab-side property.
2. Build a standalone QtADS source spike for per-area top/bottom placement,
   identifying the narrowest C++ and Python-binding API.
3. Generalize the tab bar, individual tab, title-bar composition, hit testing,
   insertion, drag thresholds, overflow, and size hints for left/right.
4. Replay the complete peer-frame docking suite with mixed tab sides.
5. Add the group command and Pyzo defaults only after the standalone behavior is
   stable.

## Allowed write surface

- Peer-frame contract, adapter, serialization, demos, and tests.
- The local QtADS source/binding checkout or an explicit fork/worktree.
- The local Pyzo project surface for final defaults and command integration.
- Root-level experiment notes and this task artifact.

## Completion evidence

Record the four-side interaction matrix, visual captures, automated commands,
application serialization examples, exact QtADS and binding source changes,
label-orientation decision, portability obligations, and whether the feature is
plausible for upstreaming or requires a maintained fork.

## Progress evidence

### Group state and serialization

The peer-frame contract now defines `TabSide.TOP`, `BOTTOM`, `LEFT`, and
`RIGHT`, stores one value on every stable group, and serializes it in layout
schema version 2. Defaults are top for editors and custom panes, and bottom for
shell, tool, and run/debug panes.

`WorkspaceModel.set_group_tab_side()` is the user-command seam. Center tab
merges retain the destination group's side. New split and floating groups
inherit the source group's side. Restore rejects unknown values atomically.

The QtADS adapter attaches tab-side metadata to each dock-area object so direct
docking changes and reverse capture preserve surviving group choices. A newly
created area inherits the prior group side of its panes. Stock QtADS explicitly
does not advertise the new rendering capability, so a requested visual change
returns `unsupported` without mutating application state.

The published stock-QtADS path remains compatible and continues to preserve
tab-side metadata without advertising visual support.

### Native top/bottom source slice

The actual Pyzo runtime package, `PySide6-QtAds`, is generated by Shiboken in
the separate `pyside6_qtads` repository around an embedded canonical QtADS
submodule. The binding repository has been added under `deps/`, and its
embedded QtADS source was advanced from the 5.0 release pin to canonical HEAD
`812ce78` before modification.

`CDockAreaWidget` now owns an `eTabPosition` value with `TabPositionTop` and
`TabPositionBottom`. Its initial value follows the existing global
`CDockManager::TabsAtBottom` flag for source and saved-layout compatibility,
but `setTabPosition()` moves the existing native tab bar for one area only.
The value is included in QtADS XML state and validated during both test and
real restore passes. Missing values in older state retain the global default.

The Shiboken type system exposes the enum, getter, setter, and change signal to
Python. Focused binding tests prove that two areas can render opposite edges at
the same time and that bottom placement survives QtADS save/restore. The
peer-frame adapter renders group `top` and `bottom` values through this API
when it is present. It intentionally still excludes the all-four-side
`TAB_SIDE` capability, so left/right requests remain atomic `unsupported`
operations instead of being rendered inaccurately.

The dependency-owned commits are QtADS `0edfe64` and PySide6-QtAds `c77dd6e`.

The macOS source build requires a matching standalone Qt SDK in addition to
the PySide wheel. The verified build used Qt 6.11.1 installed by `aqtinstall`
under `/tmp/qt/6.11.1/macos` and passed that path as `CMAKE_PREFIX_PATH`.

The deterministic suites currently pass 37 tests across their two levels:

- 17 technology-neutral contract/state-transition tests;
- 17 QtADS projection and reverse-capture tests against the fork;
- 3 direct PySide6 binding tests.

### Native left/right source slice

`eTabPosition` now also includes `TabPositionLeft` and `TabPositionRight`.
Every dock area retains its ordinary title/action bar across the top; left and
right place the existing native tab bar beside the content in a nested body
layout. Tab labels remain horizontal and readable in the vertical rail. The
rail has a 240-pixel preferred-width cap and a 120-pixel minimum-width cap so
long titles elide instead of consuming the frame or requiring rotated text.

`CDockAreaTabBar` now owns an explicit orientation. Vertical mode stacks tabs,
uses Y coordinates for hit testing and insertion, checks height for overflow,
and sends wheel events to the vertical scrollbar. `CDockWidgetTab` moves along
Y in a vertical rail and measures perpendicular X movement for undocking.

The content-layout refactor exposed one important QtADS ownership assumption:
`CDockWidget::setDockArea()` reparents a dock directly to its area. Placement
now establishes the logical area first and inserts the dock into the nested
content layout second, leaving QtADS identity intact while making the body
layout the final visual parent.

The direct PySide6 suite now passes seven tests covering simultaneous four-side
geometry, mixed-side QtADS save/restore, vertical Y-axis hit testing, Y-axis tab
reordering, X-axis undocking, and bounded/elided long horizontal labels. The
peer-frame suites pass 35 tests against both the fork and published wheel. The
fork enables the complete `TAB_SIDE` capability; published stock remains
compatible and reports four-side commands as unsupported.

The four-side dependency commits are QtADS `b5942e5` and PySide6-QtAds
`16e495e`.

The next experiment slice is interactive review of the four-side demo and
native overlay/docking behavior, followed by the Pyzo-facing group command if
that review confirms the horizontal-label rail treatment.
