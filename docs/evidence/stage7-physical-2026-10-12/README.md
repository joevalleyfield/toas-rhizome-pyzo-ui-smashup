# Windows physical checks, 2026-10-12

Task-owned two-workspace fixture launched with the native Windows Qt platform.
Snapshots come from its read-only observer; native inputs use the computer-use
tool, with user assistance for monitor configuration and Explorer delivery.

The user set portrait display LS27A70 to 150%, leaving primary at 200%, and
authorized retaining that arrangement afterward. Initial startup forced system
DPI awareness (1); its second per-monitor API call failed with E_ACCESSDENIED.
Removing those startup calls lets Qt select per-monitor awareness (2). After
restart QScreen reports device pixel ratios 2.0 and 1.5. Geometry recovery makes
the restored portrait frame reachable across Qt's mixed-DPI coordinate gap.
Mixed-DPI snapshots retain the same shared document/view identities and dirty
text in both owners. Native System/Size resizes B from width 853 to 419; all eight
menus remain available. The border-drag attempt itself did not resize the frame.

Native context menus exercise top, bottom, left and right tab placement. Native
tab reordering changes pane order without changing document resources. Native
tab drag floats shared editor-1 into frame-user-1; dragging its native title bar
docks it into A's file-browser group. Pane-floated and pane-redocked snapshots
match all pre-drag document resources exactly.

User physically disconnects portrait monitor. Observer reports one display and
retains both owners' dirty shared text. Windows minimizes B during disconnect;
native activation restores it visibly on the remaining display. Reconnect
confirmation is pending; do not infer a reconnect from successful disconnect.

User drops explorer-delivery.py from Explorer into A because the automation tool
rejects cross-application drag endpoints. Observer confirms the exact fixture
text in A, no corresponding view in B, and retained shared edits. This verifies
native Explorer drop delivery. Existing .py association points to installed
C:\Program Files\pyzo\pyzo.exe; association-based launch of this checkout was
not configured or claimed.

No display settings are restored to their prior 200% value, per user direction.
No fixture errors appeared in these recorded snapshots.

Reconnect completed, 2026-10-12: observer confirms primary DPR 2.0 and portrait
DPR 1.5. B returns to LS27A70 at reachable geometry [4430,-1279,417,661]; both
owners retain the identical shared dirty document and view identities, and no
observer errors appear. Native B File menu opens and all eight menus remain
available. Clean native Quit confirms termination of the test-owned shell;
about-to-quit reports no errors and launch supervisor exits zero. Fixture is now
closed. User's 150% portrait / 200% primary configuration remains in place.
This completes the requested mixed-DPI/reconnect/resize/Explorer/pane/tab physical
checks; resize was verified through native System/Size, not the unsuccessful
border-drag attempt. OS file-association launch was not configured or claimed.
