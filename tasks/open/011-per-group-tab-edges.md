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

The direct PySide6 suite now passes ten tests covering simultaneous four-side
geometry, mixed-side QtADS save/restore, vertical Y-axis hit testing, Y-axis tab
reordering, X-axis undocking, bounded/elided long horizontal labels, and the
non-top whole-group drag surface. The
36-case peer-frame suite passes against both dependency variants: the fork runs
35 cases with the stock-only expectation skipped; the published wheel runs 33
cases with the three fork-specific cases skipped. The fork enables the complete
`TAB_SIDE` capability; published stock remains compatible and reports
four-side commands as unsupported.

The four-side dependency commits are QtADS `b5942e5` and PySide6-QtAds
`16e495e`.

The next experiment slice is interactive review of the sides that were not
directly exercised, using the new Pyzo-facing group command, followed by real
Pyzo mixed-side workflow review.

### macOS interactive acceptance

The peer-frame demo was reviewed under the native macOS window manager. The
reviewer directly exercised a left-side vertical rail and a bottom rail and
confirmed that those visible behaviors follow the experiment contract. Native
QtADS docking feedback remained part of the interaction rather than being
replaced by application overlays.

Top and right were present in the demo's initial layout but were not directly
switched or exercised: there was no obvious user-facing side command. The
automated four-side evidence above still applies, but it is not a substitute
for interactive acceptance. A group-local `Tab position` submenu is now added
to each native QtADS group title-bar and tab context menu. It retains the
native menu entries, exposes all four choices, shows the current side with an
exclusive check mark, and applies changes through the application model so
they participate in normal persistence and re-rendering.

Experiment 011 remains open for interactive top/right switching, real Pyzo
mixed-side workflow review, accessibility/high-DPI checks, and Windows/Linux
portability evidence.

### Whole-group drag symmetry

Interactive review found that the top title-bar gutter could drag a complete
group but the corresponding surface stopped working after tabs moved to the
bottom, left, or right. This was not a tab-rail orientation defect. For non-top
positions QtADS fills the title-bar gutter with `CElidingLabel`, and that child
intercepted the gesture before the existing `CDockAreaTitleBar` drag state
machine could receive it.

The title label and the expanding `CSpacerWidget` beside it are
mouse-transparent, but interactive review established that this was not the
required affordance: users expect the whole-group grab region to remain beside
the tabs after the rail moves. QtADS shrink-wrapped the bottom tab bar to its
tabs, leaving no gutter there, while left/right already had empty vertical rail
space whose events stopped at `tabsContainerWidget`.

The bottom tab bar now expands across the available width. Empty bottom,
left, and right rail events are forwarded to the area's title bar, reusing
QtADS's existing threshold, eligibility, floating-preview, overlay, release,
context-menu, double-click, and platform paths. Events originating on actual
tabs retain their existing reorder and individual-undock behavior. Tests verify
bottom gutter geometry, press/move/release/context delivery on all three
non-top sides, and a native whole-group drag originating in the bottom gutter.
The binding development revision is `5.0.0.1.dev7`.

A future application may add a narrow explicit grab handle when tabs and title
controls consume the complete top rail and leave no free title-bar surface.
That affordance is intentionally outside this slice.

### Follow-up candidate: rail-local tabs menu

QtADS's list-all-tabs button remains part of the top title-bar composition even
after tabs move. Interactive review identified a likely requirement to colocate
that affordance with a bottom horizontal rail. Vertical rails may not need the
button because their tabs remain directly scrollable and visible; that policy
is intentionally deferred rather than being inferred by this drag fix.

### macOS rail acceptance and exposed command asymmetry

The `5.0.0.1.dev7` rail-level build was reviewed interactively on macOS. Empty
bottom, left, and right rail space now supplies the expected whole-group drag
and context-menu affordance, while actual tabs retain individual behavior. This
accepts the non-top rail interaction correction.

Closing several peer windows exposed a separate application-command
asymmetry. The remaining QtADS peer frame and its panes stayed usable, but the
Pyzo application menu—and therefore its explicit Quit command—remained owned
by the hidden `QMainWindow` service host. Closing a peer frame must not imply
application shutdown, so the native red close button correctly did not solve
that problem. The missing piece is an application-owned command surface that
is projected into every peer frame (or globally by the platform) without
making any frame privileged.

The user successfully quit an earlier layout while Pyzo's menu remained
available, but could not quit after the later close sequence removed access to
that hidden-host menu. A screenshot captured the surviving shell/tool frame;
the stranded test process and its kernel were terminated after evidence was
collected. No layout fix should make frame close and application shutdown the
same operation.
