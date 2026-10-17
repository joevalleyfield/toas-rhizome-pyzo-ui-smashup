# Native peer-frame keyboard focus

OPEN — demonstrated on Ubuntu GNOME Wayland, 2026-10-17.

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
