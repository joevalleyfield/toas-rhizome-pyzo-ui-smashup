# Linux peer-frame keyboard menus — 2026-10-15

Ubuntu GNOME Wayland, Linux aarch64, Qt/PySide6 6.11.1. This fixes the
[previously unproven keyboard menus](../linux-native-desktop-2026-10-15/README.md).

## Behavior

| Menu | Access key |
| --- | --- |
| File | Alt+F |
| Edit | Alt+E |
| View | Alt+V |
| Settings | Alt+S |
| Shell | Alt+L |
| Run | Alt+R |
| Tools | Alt+T |
| Help | Alt+H |

Existing translated mnemonics are retained; other translated titles receive
an unused character. Qt/style controls underline presentation. F10 remains
available for Pyzo's existing execute-line command.

Wayland uses one native popup surface per frame to retain its grab while
Left/Right changes root menus. Source menus retain their actions and dynamic
callbacks. Refreshes borrow the original actions, preserve surviving selection,
and avoid emptying a mapped popup. Mouse opening/hover switching uses the same
surface. Other platforms keep separate Qt menu popups. One application filter
routes only events belonging to registered peer frames. After legacy menu
commands return, queued reconciliation projects menus onto newly created frames.

## Native replay

The owned fixture used the ordinary physical acceptance setup with read-only
key logging and root-open visibility tracing. A temporary GNOME Mutter
RemoteDesktop/ScreenCast session supplied actual keyboard/pointer input and
PipeWire captures. No Qt semantic APIs drove the interactions.

Observed passes:

- All eight Alt access keys opened their respective menus; Down reached each
  popup. Underlines appeared for all eight menu titles.
- Right traversed all eight menus and wrapped Help → File; Left returned and
  wrapped File → Help. Every delayed visibility observation stayed true.
- Run → Down → Right entered Execution target. Down navigated its items;
  Left returned to Run, then Left switched to Shell.
- Escape dismissed menus. Mouse File opening and hover switching
  File → Edit → View → File kept the fixture alive and usable.
- Down/Return on File/New added one editor and frame to Physical B only.
  Physical A retained its two editors. The new frame acquired all eight menus;
  Alt+F and Down reached its File popup.
- The final fixture completed native Ctrl+Q and keyboard interpreter confirmation.

[File menu](file-menu.png) and [new frame](new-frame.png) are crops of an actual desktop capture.
[Before command](before-command.json) and [after command](after-command.json)
record workspace routing. [Native log](native.log) and [events](events.jsonl)
retain observations. The native candidate still included experimental F10 menu
entry; the final source removes that override, with a regression assertion that
F10 is not claimed by access-key routing. Alt access and arrows use the same code.

## Automated verification

The full bootstrap suite passed 816 unit tests (32 platform skips) and 27
live-kernel acceptance checks. The final full unit rerun and the 29-check focused menu/status run
passed following removal of the experimental F10 override.
[Unit receipts](units.log), [unit XML](units.xml), [live receipts](live.log),
and [live XML](live.xml) are saved alongside this file. Regression coverage includes distinct/translated mnemonics, native
QWindow key routing, wrapping/disabled roots/submenus, one-surface Wayland action
refresh, mouse opening without a second root popup, delayed submenu behavior,
post-command frame reconciliation, and destruction ordering.

This closes this bounded keyboard-menu gap. The other physical coverage limits
in the prior native acceptance record, including actual monitor reconnect,
remain unchanged. It does not establish full Linux/Stage 7 acceptance.
