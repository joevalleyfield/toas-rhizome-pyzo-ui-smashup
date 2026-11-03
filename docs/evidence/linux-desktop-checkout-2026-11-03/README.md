# desktop-ui-checkout — UTM Ubuntu ARM64, 2026-11-03

Visible replay on root `a5946d91d2ec3176ad9066b7e2f01077f80596d6`,
Pyzo `c52628c19c0b9e5edfff00de50994ccc987ce570`.

## Architecture and UI backend

The UTM Ubuntu guest reports **aarch64**, Ubuntu 24.04.5 LTS,
Linux 7.0.0-38-generic, GNOME Wayland. UI: PySide6 6.11.1 / Qt 6.11.1,
QtADS peer frames; the running fixture reports Qt platform **wayland**.
One Virtual-1 monitor, 3008 × 1692 logical pixels, device pixel ratio 1.0,
logical DPI 96. [Environment](environment.json), [runtime doctor](doctor.log).

This reuses the existing native ARM64 binding wheel
`pyside6_qtads-5.0.0.1.dev10-cp310-abi3-linux_aarch64.whl`.
It is not a fresh source build or an x86_64 build result. The historical setup
manifest predates the Python-only Pyzo focus updates; the actual checkout and
import identity are recorded independently above and in the doctor output.

## Replay

Run from the coordinating root:

```sh
python3 scripts/bootstrap.py doctor
python3 scripts/bootstrap.py launch \
  --directory /tmp/pyzo-desktop-checkout-2026-11-03 --qpa wayland
```

The first sandboxed attempt could not connect to the display socket and aborted.
The authorized desktop launch outside that sandbox succeeded. This is not
an offscreen or XWayland replay. Native GNOME Mutter RemoteDesktop key/pointer
input and ScreenCast/PipeWire capture drove the UI. The copied
[control helper](gnome-native-control.py) performs no application-object calls;
the repository physical probe only seeds the fixture and observes it.

| Check | Evidence / result |
| --- | --- |
| Visible launch and top tabs | [Maximized Physical B](b.png), [initial state](start.json). Both workspace shells reached Ready. |
| Shared edit, local cursors | Native click, Ctrl+End and typing appended `# ARM64_VISIBLE_REPLAY` to shared.py. Both views have the text; A cursor stays 0, B advances to 58. [Capture](shared-edit.png), [receipt](shared-edit.json). |
| Shared undo | Ctrl+Z removes the trailing newline in both views. A later F2/Ctrl+Z removes the final `Y` in both. The test does not claim a single undo removes the entire typed marker. [First undo receipt](shell-and-undo.json), [restored text](restored.json). |
| Local shell | F1 and native typing execute `print('ARM64_SHELL_B', 6 * 7)`; B prints `ARM64_SHELL_B 42`, A has no such command/output. [Receipt](shell-and-undo.json). |
| Menu navigation | Click File, move pointer away, Right opens Edit. [File](file-menu.png), [Edit](menu-right.png). Initial rapidly batched Alt/F/Right/Escape attempts did not establish reliable results; they are not counted as accelerator/Escape passes. |
| Local New | With editor focus, Ctrl+N creates another B editor frame; typed `# ARM64_LOCAL_B` appears only in B. [Capture](new-local.png), [receipt](local-new.json). |
| Quit cancellation | Ctrl+Q opens the live-interpreter confirmation. Click Cancel; both workspaces and both shells remain. [Dialog](quit-dialog.png), [after Cancel](quit-cancel.png), [receipt](quit-cancel.json). |
| Quit and restore | Repeat Ctrl+Q, confirm termination; supervisor exits 0. Relaunch the same fixture: both workspace identities, shared unsaved text, and B's new unsaved buffer return. [Capture](restored.png), [receipt](restored.json). This does not assert exact shell-count restoration: A has no shell after relaunch, B has one. |
| Cleanup | Final native Ctrl+Q and confirmation exit the second fixture with status 0. Both process-returned events have empty errors. Native input/capture session stopped. |

[Machine-checked receipt assertions](assertions.json), [native events](events.jsonl),
[application log](application.log), [console](console.log), [fixture IDs](fixture.json).
Only application-only captures are included; the initial full desktop capture
and final desktop cleanup capture are omitted to exclude unrelated windows.

## Acceptance scope

This adds a fresh architecture/backend/visible replay receipt to the October
Linux evidence; it does **not** close the complete Stage 7/Linux gate.
The prior [docking/scaling/drop replay](../linux-native-desktop-2026-10-15/README.md),
[menu matrix](../linux-menu-keyboard-2026-10-15/README.md),
[lifecycle/debug replay](../linux-native-lifecycle-debug-2026-10-17/README.md),
and [automatic debugger source proof](../linux-automatic-debug-focus-2026-10-17/README.md)
remain separately dated evidence, not interactions repeated today.

Still open: Stack toolbar dropdown, actual minimized-target restore,
zero-visible-frame policy, workspace creation UI, visible foreign-drop refusal,
registered OS file-association delivery, and multi-monitor reconnect/mixed-monitor
coverage. Today's one-monitor replay does not establish those results. No new
complete unit/live suite or hosted CI run is claimed by this receipt.
