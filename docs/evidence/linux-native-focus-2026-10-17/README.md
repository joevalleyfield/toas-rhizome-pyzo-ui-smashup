# Native Linux explicit peer focus — 2026-10-17

Pyzo dependency `a16b929e45d49cc6d6d493f1dadfc0329407a6eb`, based on
`25937341b1cff833a2e7539b0caf4a48e2bd8e11`. Root starting revision `5408219`.
Ubuntu GNOME Wayland / aarch64 / Qt and PySide6 6.11.1; one Virtual-1 monitor.

## Repair

Explicit View Select shell/editor now activates the target peer window before
focusing its content. Local file/new-file opens use the same helper; batch opens
with updateTabs=False do not request activation. Legacy single-window behavior
keeps ordinary focus without reordering windows. Deleted widgets, retired view
identities, teardown and targets outside the foreground workspace are refused.
The target comes from the invoking workspace facade, not global focus guessing.

The eight new guard/ordering checks and existing focus/context tests pass.
The contextual consumer inventory retains all previous 724 classifications and
adds one reviewed fixed-owner helper reference, for 725 references. The final
full unit rerun passes **825 tests, 32 platform skips**. The complete live suite
passes **27 controls**. The live run used the initial candidate including a
subsequently removed automatic-debug-source activation attempt; the final unit
rerun covers its removal and the added retired-view/batch-open guards.
[Units](units.log), [unit XML](units.xml), [live console](live-validation.log),
[live XML](live.xml).

## Native input replay

Fresh disposable fixture: `/tmp/pyzo-focus-2026-10-17`, ordinary bootstrap launch
with Wayland. GNOME RemoteDesktop supplied actual keys/pointer input;
ScreenCast/PipeWire supplied screenshots through the bounded-frame capture
helper. The normal fixture only recorded read-only snapshots/events.

- Native Ctrl+N created a separate B editor. F1 foregrounded B's shell;
  typing print("FOCUS_F1_B") executed there. F2 foregrounded B's editor;
  typing # FOCUS_F2_EDITOR_B reached only that editor.
  [Shell focus](f1-focus.json), [input receipt](f1-f2-input.json),
  [capture](f1-shell.png).
- From the shell, native Ctrl+O and GTK path entry opened focus_open.py.
  The new editor came forward without a pointer selection. Typed
  # FOCUS_OPEN_B reached its buffer. [Receipt](file-open-input.json),
  [capture](file-open-input.png).
- Opened focus_debug.py, executed F5, and entered its expected FOCUS_PM
  exception with Ctrl+P. F2 foregrounded the source editor; a marker at its end
  reached that editor. F1 returned to B's debugger shell; typed inspection
  printed FOCUS_PM_LOCAL 83. [Editor](pm-editor-input.json),
  [shell](pm-shell-input.json), [capture](pm-shell-input.png).
- A's editor/shell receipts contain none of the markers. Workspace ownership
  and interpreter targeting remained B throughout these handoffs.
- Ctrl+Shift+P stopped debugging; native Ctrl+Q and interpreter confirmation
  completed cleanly. [Events](events.jsonl) end with empty-error Quit/process
  receipts; supervisor returned zero. The input/capture session is stopped.

[Assertions](assertions.json) check these receipts. Typed editor markers were
kept as unsaved disposable fixture content; no user document was involved.
An attempted Alt+F9 minimization did not establish minimized-window state, so
restoration of minimized targets has unit coverage only and is not a native pass.

## Remaining limitation

Automatic source foregrounding from an asynchronous debugger response remains
unaccepted. In the candidate, activateWindow after the kernel reply did not
bring the source ahead of the shell. The final change does not add that
unsuccessful activation attempt. F2 is the verified explicit handoff after PM
entry. Toolbar Stack popup, physical reconnect and the other outstanding Linux
acceptance obligations remain as recorded in the previous replay.

## Source handoff

The dependency commit and root pin are local; no repository was pushed.
The [Git bundle](pyzo-focus.bundle) carries the exact new dependency commit with
the recorded base as prerequisite. For an existing baseline Pyzo checkout,
fetch HEAD from this bundle and check out the manifest's new SHA before offline
bootstrap reuse. The [patch](../../patches/native-peer-focus.patch) records the
same source/test delta. A fresh online bootstrap cannot fetch the new SHA from
GitHub until the dependency commit is published; seed from the bundle meanwhile.
