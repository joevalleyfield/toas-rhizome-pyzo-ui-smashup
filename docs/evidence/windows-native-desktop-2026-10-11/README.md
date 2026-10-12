# Native Windows desktop replay — 2026-10-11

Windows 11 x64, Python 3.12.13, Qt/PySide6 6.11.1, locally built QtAds.
Interactions used actual Windows Qt windows and native input. Fixture snapshots
are observations, not substitutes for native input.

Verified: independently discoverable workspace windows; minimize/restore;
maximized and 850-pixel menu layouts showing all eight menus; splitter resize;
shared editor typing, undo and redo; shell creation with complete menus;
real Python shell output; restart cancel; successful normal restart with a new
PID and retained dirty shared text; native Open dialog owner routing; a new local
file and owner-scoped Run; normal Quit and persisted shared/local text.

Final restart: PID 24868 -> 32080, recorded in before-final-restart.json and
after-final-restart.json. Final native supervisor quit status was zero. Saved
workspace state retains shared_native_value = 42 and native_local_value = 73.
The source file was not overwritten merely to retain dirty buffers.

PDF export through the native menu, preview and Save dialog created
native-export.pdf (15,492 bytes). QPdfDocument loaded it successfully with one
page; extracted text contains the shared editor contents. The log retains
nonfatal first-chance COM diagnostics during PDF interaction. This verifies
creation/content, not every visual export layout.

The event log includes exploratory runs that exposed startup-order and shutdown
refresh errors. before/after-corrected-restart.json is intermediate evidence;
before/after-final-restart.json is the final clean handoff. The later rejected
transient-owner experiment is not the accepted implementation.

Fixes: real Windows floating frames use independent native ownership and a
minimize button while retaining their QtAds manager; every loaded runtime watches
settled chrome updates; command refresh after completed exit stops when no frame
projection remains. Render-generated focus avoids global affiliation work.

Remaining physical checks: mixed-DPI/multiple monitors, OS file association and
Explorer drop delivery, all tab positions and cross-window pane dragging. No
Developer Mode or symlink privilege was enabled. Stage 7 is not fully accepted.
