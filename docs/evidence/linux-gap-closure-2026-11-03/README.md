# Linux desktop acceptance gap closure — 2026-11-03

UTM Ubuntu 24.04.5, aarch64, GNOME Wayland, Qt/PySide6 6.11.1,
QtADS peer frames. Root parent `a5946d9`; final Pyzo pin
`96abf9439711ee976d34b6e08dcc85a5496b79b7`.
This continues the [fresh checkout](../linux-desktop-checkout-2026-11-03/README.md)
and the October native evidence. It closes the previously enumerated desktop
checklist gaps on this guest, not every requirement or platform combination.

## Repairs

- File → **New workspace...** now exposes the existing application-owned
  creation operation in peer menus. Cancel/blank input creates nothing;
  confirmed names are trimmed. The new workspace gets its own identity/editor,
  without borrowing another workspace's interpreter.
- Cross-workspace QtADS drags now show **“Panes stay in their workspace.
  Open the file here to create a local view.”** The event is refused before
  projection changes. QtADS checks the source against the target manager's
  live registry; permitted same-workspace drags continue normally.
- The physical observer skips committed shutdown and stops its timer on Quit,
  avoiding observations of already retired runtime IDs. It also records zero
  remaining frames at Quit. These are test-fixture changes, not UI automation.

## Visible results

All UI actions used native GNOME RemoteDesktop keyboard/pointer input.
ScreenCast captured compositor pixels; application snapshots are read-only.
Some captures are cropped to application bounds to exclude unrelated windows.

| Former gap | Passing native evidence |
| --- | --- |
| Stack toolbar dropdown | Executed stack_source.py, entered PM with Ctrl+P, clicked Stack (2/2), then selected frame 1. The popup shows both source frames; B receives `DB FRAME 1` and selects the module source line. A receives no debugger command. [Popup](stack-open.png), [source selection](stack-frame1.png), [receipt](stack-frame1.json). No Stack production repair was required. |
| Workspace creation UI | Clicked File → New workspace..., named it Native C, typed `# NEW_WORKSPACE_C`. A/B remain unchanged; C has its own editor and no implicit shell. [Menu](new-workspace-menu.png), [capture](workspace-created.png), [receipt](workspace-created.json). |
| Minimized target restoration | Minimized the separate B source frame using GNOME Alt+F9, then restored it with F2 from B's shell and typed `# MINIMIZED_RESTORE_INPUT` into that source. Repeated with the native title-bar minimize button and F2. [Minimized](title-minimized.png), [restored](title-restore.png), [input receipt](fixed-final.json). C's independently minimized window was not raised. Mutter does not report compositor minimization through Qt's isMinimized flag here; the captures and input delivery establish this result. |
| Foreign-drop refusal feedback | Dragged A's local tab over B's association_os.py window. The refusal tooltip is visible, and the pane remains in A, floated rather than transferred. [Capture](foreign-feedback.png), [ownership receipt](foreign-drop.json). |
| Actual OS association delivery | Registered text/x-python → pyzo-acceptance.desktop in temporary XDG data/config directories. `gio mime` selects it; `gio open .../association_os.py` launches its handler and the running fixture's production command handler opens the file in foreground B only. [Capture](association-os-delivered.png), [OS handler receipt](association-launch.json), [owner receipt](association-os.json). See isolation details below. |
| Native zero-frame policy | Closed B and then A using window-manager close, confirming interpreter termination. The application emits about-to-quit with `remaining_frames: 0`, empty errors, then process-returned. Linux exits rather than retaining an unreachable windowless app. [Final close](final-frame-close.png), [events](monitor-zero/events.jsonl). A separate standard-fixture replay also returned status 0: [events](zero-initial/events.jsonl). No Linux reopening-from-zero behavior is promised by this policy. |
| Guest monitor disconnect/reconnect and mixed scale | Created a real second Mutter Wayland output, moved B with Super+Shift+Right, disconnected it, and typed `HOTPLUG_INPUT` into B on the surviving output. Reconnected, applied primary 100% / secondary 200%, moved/maximized B there, typed `MIXED_DPI_INPUT`, then disconnected again and typed `RECONNECT_CYCLE_DONE`. [Second output](second-monitor-frame.png), [mixed-scale capture](mixed-dpi-maximized.png), [DPR receipt](mixed-dpi-input.json), [final one-output/input receipt](reconnect-complete.json). |

[Machine-checked assertions](assertions.json) check identity, local input,
foreign ownership, native screen/DPR changes, and final zero-frame Quit.
Full logs are grouped by owned fixture: [Stack](stack/),
[workspace/minimize](workspace-minimize/), [association/drop](association-drop/),
[monitor/zero-frame](monitor-zero/).

## Reproduction and isolation

Use the normal launcher with a fresh fixture and explicit Wayland:

```sh
python3 scripts/bootstrap.py launch --directory /tmp/pyzo-replay --qpa wayland
```

For the OS association replay, the physical fixture optionally enables the
unchanged production command handler at a fixture-only endpoint:
`PYZO_PHYSICAL_SERVER_ADDRESS=localhost:pyzo-association-2026-11-03`.
Only the command module's address constant is replaced by the harness; the
user's `localhost:pyzoserver` is never contacted. The
[desktop entry](pyzo-acceptance.desktop), [temporary default](mimeapps.list),
and [Exec bridge](pyzo-association-launcher.py) are retained. Set XDG_DATA_HOME
and XDG_CONFIG_HOME to those isolated directories for `gio mime`/`gio open`.
Keep the launching command alive for two seconds: gio returns before its child
has delivered the request, and the command runner otherwise reaps that child.
The first bridge trial also needed its yoton import path corrected; the accepted
OS-only filename was never opened by the direct-launch diagnostic.
No user-wide MIME association was modified.

[Virtual monitor helper](gnome-virtual-monitor.py) uses Mutter RecordVirtual
and a variable-rate PipeWire stream with fixed 1920×1080 dimensions.
[Mutter's interface](https://raw.githubusercontent.com/GNOME/mutter/gnome-46/data/dbus-interfaces/org.gnome.Mutter.ScreenCast.xml)
represents this as a native virtual monitor. The first fixed-framerate trial
negotiated no monitor; it is not counted. Input is driven by the original native
control session; the virtual helper is used only for output lifetime/capture.
[Mixed-scale helper](gnome-mixed-scale.py) applies a temporary layout; removing
the owned stream restores the original single 3008×1692 output at DPR 1.
The first layout call tried an unsupported layout-mode property and was
rejected without applying a configuration; the successful call preserves the
existing mode. All input/capture streams and fixture applications are stopped.

This is native **guest virtual-output** hotplug, not a physical host cable,
UTM device reconfiguration, or electrical-monitor test. It verifies actual
QScreen/DPR changes and compositor behavior rather than mocked screens.

## Verification and retained limitations

Final units: **831 passed, 32 platform skips, 2 warnings**.
[Console](final-units.log), [JUnit](units.xml).
The complete live suite on the same product changes: **27 passed**.
[Console](validation.log), [JUnit](live.xml).
The added drop test checks real QtADS source membership: foreign manager refusal
with feedback, unchanged model, and no interference with a permitted local drag.
[Focused result](drop-tests.log). The contextual ownership review is updated.

The initial sandboxed live-suite attempt could not use its kernel/socket
resources and did not finish successfully; [log](sandbox-attempt.log).
The successful live replay ran with the required process/socket access.
An initial last-frame run exposed a read-only observer race after runtime
retirement; the guard above fixes it. The final native events have no observer
or application cleanup errors. The outer command runner reported 143 on the
association and monitor supervisors after their sessions; the monitor application
itself records both clean about-to-quit and process-returned. The independent
standard zero-frame supervisor returned 0. We do not present the association
supervisor as a successful clean-exit proof.

The prior seven gaps now have native evidence or the two concrete UI repairs.
The overall Stage 7 requirement/platform matrix remains separate; Windows/macOS
native replay and physical host monitor behavior are not inferred from this run.

## Hosted follow-up: native mnemonic policy

Inspecting the previous checkpoint's retained macOS artifact exposed a failure
in `test_all_application_menus_have_distinct_expected_mnemonics` on run
39135156444. Qt returns empty native mnemonic sequences on macOS. Marker
assignment had used that platform result to detect existing title markers,
which could repeatedly add ampersands and overwrite translated choices.
The adapter now parses explicit Qt `&` markers independently, respecting
escaped `&&` and preserving existing translated access keys. A regression
forces empty native mnemonic lookup and proves repeated assignment is stable.
Actual Option-key dispatch still uses Qt's native policy; its synthetic Alt
test is inapplicable on macOS and is explicitly skipped there. Linux/Windows
continue to test the native Alt dispatcher. Focused menu suite: 22 passed.
