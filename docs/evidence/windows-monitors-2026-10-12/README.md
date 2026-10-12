# Physical multi-monitor Windows replay — 2026-10-12

Two displays were detected: primary landscape 1920x1080 logical, and LS27A70
portrait 1728x3072 logical, located above/left at negative desktop coordinates.
Both reported device pixel ratio 2.0 (200%); logical DPI 96. No system display
settings were changed. This is equal-scale multi-monitor evidence, not mixed DPI.

The user manually moved Physical B to the second display because the automation
helper bounds drags to its current window and forbids Windows-key shortcuts.
The read-only fixture observer confirmed Physical A on DISPLAY1 and Physical B
on LS27A70. Native input then verified maximize/restore on LS27A70, all eight
menu labels, File popup placement, and minimize/restore without losing that screen.

Native typing in B's shared editor propagated to A on the primary display.
Native Ctrl+Z in A restored the original shared text in both views. Snapshots
retain document/view identities and monitor assignment for these effects.
The maximized geometry changed to 1728x3050 logical; restore returned to 850x650.

A border-resize attempt and native keyboard-size interaction through the helper
did not produce an observable resize; this subcontrol is unverified. These helper
limitations are not evidence of an application resize defect. Mixed-DPI transitions,
monitor removal/reconnect, OS file association/Explorer drop and native pane/tab
interactions remain open. Native Quit completed with supervisor exit status zero.
No new production repair was needed for the checks performed.

Observer-only source changes record screen geometry/scaling and each frame's
screen/device pixel ratio. Syntax compilation and source whitespace checks pass;
no full application suite was rerun for read-only observation fields.
