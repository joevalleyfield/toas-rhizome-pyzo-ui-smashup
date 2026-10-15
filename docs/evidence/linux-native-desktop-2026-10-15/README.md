# Native Linux desktop replay — 2026-10-15

Tested coordinator `e2a62a1`, with the dependency revisions recorded in the
[automated validation](../linux-top-tabs-2026-10-15/validation.md). Ubuntu GNOME,
Wayland, Linux aarch64, Qt/PySide6 6.11.1. One QEMU Virtual-1 monitor, initially
3008×1692 at 100%. This is an actual desktop replay, not an offscreen run.

Fixture: `/tmp/pyzo-native-acceptance-2026-10-15`, launched with
`python3 scripts/bootstrap.py launch --directory PATH --qpa wayland`.
The browser-control tool does not expose native applications. Instead, a
temporary local GNOME Mutter RemoteDesktop/ScreenCast session supplied native
pointer/button/key input and PipeWire screenshots. No Qt semantic docking APIs
were used for the interactions below. The standard fixture supplied read-only
snapshots and event observations. The control/capture session is now stopped;
the fixture completed clean Quit. No production source changed in this replay.

## Observed results

| Check | Result and evidence |
| --- | --- |
| Shared edit and undo | Native typing in A appeared in both shared views; native Ctrl+Z in B removed the last character in both. Views remained distinct and shared one document. |
| Native top-tab reorder | A's `[editor-1, editor-2]` became `[editor-2, editor-1]`; [reordered](reordered.png). |
| Float | Native tab drag created A's `frame-user-1` containing the existing shared pane; [floated](floated.png). |
| Split/redock | Dragging the floating tab to A's lower split target produced two editor groups in its original frame; [split](split-redock.png). |
| Four tab positions | Native context menu changed the shared group Top → Left → Right → Bottom; a bottom-rail drag redocked it into A's Top group. [Left](left-tabs.png), [Right](right-tabs.png), [Bottom](bottom-tabs.png). |
| Foreign workspace drop | Dragging A's Left tab over B did not add it to B. The pane floated as A's `frame-user-2`, retaining its view/document/owner. The visible no-drop/refusal cue was not captured, so that UX criterion remains unproven. |
| Foreground File/Open | Native Ctrl+O in B opened the GTK file chooser; double-clicking `ingress.py` created B's view only. |
| Desktop file-manager drop | GNOME Files opened the fixture folder. Dragging its `ingress.py` icon into A's editor created A's view of the same document already open in B. Separate view identities verified in snapshots. No file association was installed. |
| Native shell keyboard execution | After focus settled, typing and Return executed `print('native_B_keyboard')` in B only. A's shell did not receive that marker. |
| Border resize | Actual right-border drag increased A's width from 640 to 883 logical pixels. |
| Actual display scale | A temporary GNOME display change to 200% yielded a 1504×846 logical screen and DPR 2.0 in every fixture frame, with no observer errors. Original mode and logical configuration were restored; frames returned to DPR 1.0. [Scaled snapshot](display-200.json), [restored](display-restored.json), [original configuration](gnome-display-before.json), [final configuration](gnome-display-after.json). |
| Quit cancellation | Native Ctrl+Q opened interpreter confirmation; Escape cancelled, preserving the fixture. |
| Native Restart | Selected Restart in the [native File menu](native-file-menu.png), confirmed interpreter termination, and observed startup again with a reset observer sequence. Every owner/view/document identity and unsaved text survived. [Before](before-restart.json), [after](after-restart.json). |
| Quit / fresh relaunch | Confirmed Quit and observed supervisor exit 0. Relaunched the same fixture into a different PID; all owner/view/document identities and text matched. [Fresh process](after-relaunch.json). Final Quit was confirmed using Shift+Tab and Space in its dialog; supervisor again exited 0. |

[Assertions](assertions.json) compare the receipts: shared/canonical document
identities, distinct local views, exact per-view retained text across Restart
and fresh relaunch, B-only shell output, actual DPR transitions, original
display configuration restoration, and two clean Quit event pairs. Both
`about-to-quit` and `process-returned` report empty error lists. Restart uses
exec and does not produce a normal Qt Quit event pair.

The complete [observer events](events.jsonl) contain 115 native mouse receipts.
[Console](console.log) retains startup, Restart and relaunch output. Screenshots
are crops of actual desktop captures, excluding unrelated applications.

## Keyboard gap and coverage limits

**Ctrl+Tab did not switch the peer editor group or show editor history**, even
after repeating with focus settled in A's two-editor group. The [capture](ctrl-tab-no-switch.png)
shows the group remained on shared.py. Source inspection finds the legacy
forwarding call in `deps/pyzo/pyzo/core/main.py:MainWindow.keyPressEvent`; the
peer pane focus filter handles FocusIn only. `EditorTabs.processKeyPressFromMainWindow`
also builds history from a single EditorTabs host, whereas peer panes are
separate hosts. This is a concrete acceptance gap, not an accepted native
keyboard traversal result. It needs a workspace-aware peer keyboard route and
an explicit selection/history policy; no ad hoc production change was made
during this validation-only slice.

F10/Alt+F menu activation and arrow-menu traversal were attempted without a
successful observed result, so keyboard-only menu availability remains
unproven. Ctrl+O, Ctrl+Q, Ctrl+Z, ordinary shell typing/Return, Escape cancellation,
and dialog Shift+Tab/Space did work. Mouse-operated File and tab-position menus
worked. These partial passes do not accept complete keyboard navigation.

The first input helper sequence typed immediately after clicking a different
window: its initial `p` went to the prior editor, leaving `rint(...)` in B's
shell and an expected NameError. The replay was repeated with a focus-settle
pause, then B executed the full command correctly. This helper artifact is
retained in the snapshots/shell text and is not classified as an application
failure. It explains the retained extra `p` in ingress.py. Likewise, the first
display request included an unsupported explicit layout-mode property; GNOME
rejected it without changing configuration. The successful retry omitted that
property and automatically restored the original configuration.

Physical multi-monitor/reconnect is unavailable in this one-monitor guest.
Actual OS file-association delivery was not configured or exercised. Native
zero-visible-frame activation, confirmed individual live-shell/frame closure,
new-workspace/new-shell menu flows, the complete native Run/debug/postmortem
workflow, and foreign-drop refusal messaging are not accepted by this bounded
replay. Their automated controls retain the prior passing evidence; automation
does not substitute for these physical obligations. Wayland compositor window
placement also means Qt's reported global frame positions are not reliable
proof of exact restored desktop placement.

The Linux/Stage 7 gate stays open, with keyboard traversal now a reproduced
blocker. The tab visibility repair and inset remain validated independently.
