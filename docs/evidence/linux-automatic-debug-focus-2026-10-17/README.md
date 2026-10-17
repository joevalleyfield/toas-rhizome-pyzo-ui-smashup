# Automatic debugger source foregrounding — 2026-10-17

Ubuntu GNOME Wayland, aarch64, Qt/PySide6 6.11.1. Root base `0fbd8d8`;
Pyzo base `a16b929e45d49cc6d6d493f1dadfc0329407a6eb`, repaired dependency
`c52628c19c0b9e5edfff00de50994ccc987ce570`.

## Change

After DebugStack resolves the session-owned source, navigates to its line, and
finishes selecting that line, it explicitly calls the guarded focus_widget
handoff. This covers asynchronous breakpoint/postmortem updates as well as
stack-source navigation. Existing session/epoch checks precede navigation;
foreground workspace, teardown and retired-widget guards precede activation.
Background workspaces cannot request source activation through this helper.

The earlier attempted handoff inside the source opener ran before DebugStack's
final navigation/selection. This final placement is independently verified
below; no private Wayland API or compositor override is used. Failed or stale
navigation never calls the source focus helper.

## Native proof

Owned fixture `/tmp/pyzo-auto-debug-2026-10-17`, with the normal physical probe
and read-only focus tracing around the real helper. The tracer prints requested
owner, foreground owner and native active window 200 ms later; it performs no
focus/activation itself. Native GNOME RemoteDesktop key/pointer input drives
all actions, with bounded-queue ScreenCast captures.

- Opened auto_source.py and executed its intentional AUTO_SOURCE_PM exception.
  F1 selected B's shell; Ctrl+P entered postmortem. The kernel reply brought
  auto_source.py ahead of the shell, selected the failing line, and focused its
  editor without F2 or a source-window click. [Snapshot](automatic-pm-source.json),
  [capture](postmortem-source.png).
- A subsequent postmortem replay followed by Ctrl+End and native typing put
  # AUTO_PM_INPUT in that source buffer. [Receipt](automatic-pm-input.json).
- auto_break.py sleeps two seconds before its breakpoint. F5 started it, then
  F1 foregrounded the running B shell. The breakpoint reply foregrounded
  auto_break.py and focused its editor. The trace records PythonShell/Running
  before the reply and PyzoEditor/auto_break.py afterward.
  [Snapshot](automatic-live-source.json), [capture](breakpoint-source.png).
- Repeated the delayed run, selected A while B slept, and focused A's editor.
  B reached Debug while A kept editor focus and its active window. No source
  window in B was activated. [Receipt](background-no-steal.json),
  [capture](background-no-steal.png).
- Native Ctrl+Q and interpreter confirmation ended the fixture with zero exit
  and empty cleanup errors. The control/capture session is stopped.

[Assertions](assertions.json), [focus log](application.log), [events](events.jsonl).
Extra timing/input trials remain in the logs: one typed live marker stayed at
the shell prompt, and a later replay executed the wrong selected source and
never hit the expected breakpoint within ten seconds. These are not counted as
passes. The passing live proof is the captured delayed breakpoint handoff;
postmortem source typing is independently asserted. No source buffer was saved
by these marker checks.

## Validation and handoff

Two regressions check that focus follows final line selection and that stale
source navigation requests no activation. The existing eight explicit focus
ownership/lifetime checks remain. Complete bootstrap: **827 unit tests passed,
32 platform skips; all 27 live checks passed**.
[Console](validation.log), [units](units.xml), [live](live.xml).
Initial standalone test setup lacked QApplication/config; those test-fixture
imports were corrected before the successful focused and complete suites.

The ownership census retains 725 references and prior classifications, with
updated reviewed function hashes. The dependency commit/root pin are local;
nothing was pushed. [Bundle](pyzo-debug-focus.bundle) exports the exact commit,
requiring the preceding a16b929e dependency commit (available in the preceding
focus evidence bundle). [Patch](../../patches/automatic-debug-source-focus.patch)
records the same delta. Seed the bundle before fresh offline bootstrap reuse;
GitHub cannot supply the new pin until it is published.

This repairs the automatic source foregrounding gap in the exercised Linux
cases. It does not accept the toolbar Stack popup, minimized-window restore,
monitor reconnect, other native platforms, or the broader Linux/Stage 7 gate.
