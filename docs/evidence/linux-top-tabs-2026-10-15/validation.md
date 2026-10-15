# Tab/chrome validation, 2026-10-15

Scope: proof the top-tab repair (`0e81884`) and right/bottom inset (`119cf19`)
against the existing acceptance suites. This receipt does not close the complete
Stage 7 physical-desktop gate.

Environment: Linux aarch64, Python 3.12.13, Qt/PySide6 6.11.1, native Wayland
for the visible QtADS tests; offscreen for the bootstrap acceptance harness.
Dependency revisions:

- Pyzo: `25937341b1cff833a2e7539b0caf4a48e2bd8e11`
- Binding: `764eb4a487abccb162dcbee1a8f0383916561e0e`
- QtADS: `244157db5bdffdf9d250e58a6edf8ee6acfd3a61`

## Focused proof

The new status/chrome regression exercises all four tab sides, returns to Top,
resizes through 800×500, 500×350 and 1100×700, toggles status visible/hidden/
visible, and saves/restores native layout. It checks actual rail and individual
tab rectangles remain inside the frame and clear of menu/status overlays.
Restored tab geometry is checked again. This complements the earlier top-tab
test's demonstrated failure against the original chrome helper.

| Replay | Result | Log |
| --- | --- | --- |
| Native Wayland adapter + menus + status | 56 passed, 2 skipped | [log](wayland-docking.log) |
| Native Wayland menus/status, forced 125% | 23 passed | [log](wayland-scale125.log) |
| Native Wayland menus/status, forced 200% | 23 passed | [log](wayland-scale200.log) |
| Offscreen menus/status, forced 125% | 23 passed | [log](offscreen-scale125.log) |
| Offscreen menus/status, forced 200% | 23 passed | [log](offscreen-scale200.log) |

The two adapter skips are the stock-binding-only fallback and Windows-specific
native ownership. Forced scale factors exercise Qt scaling, not a physical
monitor reconnect or a change to the desktop's display settings. Native tests
exercise semantic QtADS operations, not physical mouse dragging.

Compilation of the touched Python files and `git diff --check` pass. No
dependency sources, requirement assertions, timeouts, or production ownership
rules changed in this validation slice.

## Full bootstrap acceptance

`python3 scripts/bootstrap.py test` exits zero outside the socket-restricted
sandbox: **810 passed, 32 skipped, 2 warnings** in 12.13s for units, followed
by **27 live controls passed** in 215.73s. The warnings are the existing Qt
high-DPI attribute deprecations. The live suite explicitly enables the controls
skipped by the default unit invocation and covers real retention, workspace
restore, shared documents, affinity/smoke failure controls, Run/selection,
debugger, provenance, tools, 1/4/8-workspace scaling, execution, and pristine/
legacy/peer profile compatibility.

Retained receipts: [full console](bootstrap-validation.log),
[unit JUnit](units.xml), [live JUnit](live.xml).

The initial sandbox attempt passed 809 units before the added geometry test,
then failed to create kernel TCP sockets (`PermissionError: Operation not
permitted`). A [focused failure receipt](sandbox-socket-control.log) establishes
that restriction. The redundant sandbox run was terminated; it is not counted
as an application regression or a passing live run. The unrestricted full run
above is the acceptance result. No deadlines or success checks were relaxed.

## Remaining physical coverage

The visible screenshots in [the repair record](README.md) establish the original
overlap and the repaired top tabs/inset. Automated native Wayland geometry and
adapter operations pass. Remaining physical acceptance includes actual tab/rail
drag and redock gestures, foreign-workspace drops, native file-manager delivery,
keyboard/focus/menu traversal, and available display changes. This session's
computer-control tools do not expose native desktop interaction; these checks
remain manual and are not inferred from the automated passes. Windows/macOS
were not replayed here. The execution checklist's Stage 7 NEXT marker stays open.

Follow-up on 2026-10-15: a local GNOME Mutter input/capture session enabled an
[actual native replay](../linux-native-desktop-2026-10-15/README.md), covering
tab reorder/float/split/redock, four tab positions, desktop file drop, border
resize, real display scaling, and native Restart/Quit/relaunch. It reproduced
a peer Ctrl+Tab gap; keyboard-only menus and the remaining physical limits are
listed explicitly. That later receipt supersedes the tooling limitation above
without treating every physical criterion as accepted.
