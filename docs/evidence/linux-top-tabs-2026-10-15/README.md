# Linux top pane tabs

2026-10-15, Linux aarch64, Qt 6.11.1, native Wayland.

The basic QtADS layout spike renders top tabs correctly. The integrated physical
fixture reproduces the reported absent top tabs: the tab bar is visible according
to Qt, but the application's overlay menu occupies the same frame coordinates.
See [before](before.png) and [after](after.png).

Linux QtADS floating frames derive from QDockWidget. Its private layout does not
place the dock content below the frame contents-margin reservation used by our
menu/status projectors. The shared chrome helper now also reserves these edges
inside the QDockWidget content, preserving the original content margins and
recomputing reservations without accumulation. Other frame types keep the
existing path. No QtADS or Pyzo dependency source changes are needed.

`test_top_tabs_do_not_overlap_frame_menu` checks actual tab geometry against the
projected menu. It fails against the original helper and passes with the fix.
Offscreen menu/status suites: **22 passed**. Fresh integrated native Wayland
fixture visibly shows top tabs beneath the menu, including the shared/local
editor group. This confirms this visual repair, not the complete desktop
acceptance checklist or all tab dragging/position transitions.

The fixed fixture is `/tmp/pyzo-top-tabs-fixed`; diagnostic reproduction is
`/tmp/pyzo-top-tabs-diagnostic`. Both use isolated generated profiles. Images
were captured from the actual integrated windows using QWidget.grab().
