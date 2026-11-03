# Native peer-frame keyboard focus

FOCUS REPAIR COMPLETE — bounded Ubuntu GNOME Wayland replay, 2026-10-17.

F1 / View Select shell does not foreground/focus a separate shell window after
editor-side debugging. A subsequent typed command reached the editor. Ctrl+O
from the shell opened an editor behind the shell rather than activating it.
Evidence and exact receipts: [native continuation](../../docs/evidence/linux-native-lifecycle-debug-2026-10-17/README.md).

Investigate application-owned peer activation for Select shell/editor, file-open
and debugger source navigation. Verify native compositor activation, actual
focus and typed-input delivery between distinct editor/shell peer frames while
preserving workspace identity. Do not treat setFocus alone or offscreen tests as
proof of native foreground activation. Preserve Ctrl+Tab's user-confirmed pane
cycling and editor Tab indentation. The toolbar Stack dropdown also remains
unproven; console DB FRAME selection and PM local inspection passed.


Explicit F1/F2 and local file-open handoffs repaired in Pyzo a16b929e.
[Native proof](../../docs/evidence/linux-native-focus-2026-10-17/README.md)
verifies actual marker delivery to separate B shell/editor windows, including
postmortem, with no A markers. 825 final units and 27 live controls pass.

Remaining: asynchronous debugger source foregrounding and the toolbar Stack
popup are unaccepted. Native minimized-target restore was not established;
only guard/ordering tests cover it. The broader Linux gate stays open.


Automatic debugger source foregrounding repaired in Pyzo c52628c1.
[Native delayed-breakpoint/postmortem proof](../../docs/evidence/linux-automatic-debug-focus-2026-10-17/README.md)
verifies source-window activation, PM typing, and preservation of A's focus when
B hits a background breakpoint. 827 unit tests and 27 live checks pass.
This completes the demonstrated explicit/automatic focus repairs. Stack popup,
minimized-target native restore and the broader platform gate remain outside
this accepted repair coverage.


2026-11-03: [Native gap closure](../../docs/evidence/linux-gap-closure-2026-11-03/README.md)
now proves the toolbar Stack dropdown/selection and minimized-source F2 restore.
The historical unaccepted statements above are superseded for the tested UTM
Ubuntu aarch64 GNOME Wayland combination.
