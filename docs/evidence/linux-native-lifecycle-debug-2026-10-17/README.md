# Linux native lifecycle/debug continuation — 2026-10-17

Ubuntu GNOME Wayland, Linux aarch64, Qt/PySide6 6.11.1, one Virtual-1 monitor.
Starting source: `770125a`. Fresh isolated fixture launched with
`python3 scripts/bootstrap.py launch --directory /tmp/pyzo-acceptance-2026-10-17 --qpa wayland`.
It was cleanly Quit and relaunched once for the adapter repair, then cleanly Quit
at the end. Both exit event pairs report no cleanup errors.

## Observed native results

| Check | Result |
| --- | --- |
| Shell menu creation | Shell → Create shell 1 added a second live interpreter and separate shell frame to B. A remained unchanged. [Capture](new-shell.png), [snapshot](new-shell.json). |
| Individual shell Cancel | Alt+K opened interpreter confirmation. Escape preserved exact B editor/shell receipts and A. [Dialog](close-dialog.png), [cancelled](close-cancelled.json). |
| Individual live frame close | Native X on the new shell frame opened the same confirmation. Shift+Tab/Space confirmed termination. Only the new B shell disappeared; A's existing shell/editors and B's other shell survived. [Receipt](shell-closed-file-opened.json). |
| Ctrl+O / new editor chrome | GTK file open created an editor in B. Before repair its new frame lacked menus. After repair a fresh Ctrl+O open of acceptance_open.py received all eight menu titles; after selecting its window, Alt+V opened View. [Capture](keyboard-open-chrome.png). |
| Live Run/debug | Opened [fixture source](fixture-run.py), moved to line 2, Ctrl+B set a breakpoint, F5 executed the file in B. Shell entered Debug at acceptance_probe. Shell → Debug next issued DB NEXT; Shell → Debug continue issued DB CONTINUE. Output reached ACCEPTANCE_RUN 42 and the expected RuntimeError: ACCEPTANCE_PM. [Breakpoint](live-breakpoint.png), [receipt](live-breakpoint.json). |
| Postmortem | Ctrl+P entered acceptance_failure. Native shell typing inspected pm_value and printed ACCEPTANCE_PM_LOCAL 73. DB FRAME 1 selected the parent, where inspection printed ACCEPTANCE_PM_PARENT 42. DB FRAME 2 returned to the failing frame. Ctrl+Shift+P stopped debugging and shell returned to Ready. [Capture](postmortem.png), [local](pm-local.json), [parent](pm-parent.json), [stopped](fresh-open-chrome.json). |
| Clean application quit | Native Ctrl+Q and interpreter confirmation terminated the isolated fixture; supervisor exited zero. [Events](events.jsonl) end with empty-error about-to-quit/process-returned. |

[Assertions](assertions.json) check saved workspace/shell/editor receipts.
The fixture source intentionally raises; this is expected kernel output.

## Repair and verification

QtADS creation signals occur inside adapter render, while observers are
suppressed and before the model commits. A render with no activation request
never scheduled the settled observer notification. The adapter now coalesces a
next-turn notification in this case, allowing all loaded-workspace chrome
projectors to reconcile the committed frame set. No layout recapture/adoption
is introduced just to notify observers; existing activation synchronization and
retirement guards remain intact.

The new regression checks deferred notification, committed model/frame identity,
and zero native adoption. It fails on the original adapter
([negative control](pre-fix-regression.log)) and passes with the repair.
Focused backend/menu/status checks: **63 passed, 2 platform skips**.
Full bootstrap: **817 passed, 32 platform skips; all 27 live checks passed**.
[Console](validation.log), [units](units.xml), [live](live.xml).

## Failures and coverage limits

**Cross-window keyboard focus remains a demonstrated failure.** After live
Debug next, F1 did not foreground/focus the separate B shell. Native typing
landed in the editor instead. [Receipt](f1-focus-failure.json) records editor
focus, the unintended disposable source edit, and a Debug shell without the
marker. File → Reload from disk and its explicit confirmation restored the
source exactly before subsequent checks. Ctrl+O from the shell also left the
shell in front of the opened editor. Native window selection was needed to
inspect its chrome. This is separate from successful pane cycling reported by
the user and from the repaired post-render chrome notification.

The toolbar Stack dropdown did not produce a usable observed menu in this
replay; its menu-specific interaction remains unproven. Frame selection through
the shell's normal DB FRAME commands is covered above. The log retains four
parser diagnostics (`NoneType ... tokens`) after the accidental edit; they are
not classified as acceptance passes or silently removed.

Screen capture eventually accumulated latency in its PNG pipeline. Later
coordinate trials are not used as proof of new application behavior. The capture
session was restarted with a bounded leaky frame queue, and the final unique
acceptance_open.py window was selected through GNOME's application window list
before capturing its menu. The fresh final capture is used for chrome proof;
read-only snapshots establish the earlier shell/debug results.

Workspace creation via a native menu, zero-visible-frame activation, actual OS
file-association delivery, foreign-drop refusal messaging, physical monitor
reconnect and the complete platform/requirement matrix remain unaccepted.
No workspace-creation menu flow is claimed. A has no live shell after the
intermediate application restart; invariants before that restart are compared
only within that process. The kernel is not claimed to survive restart.
The isolated fixture and both remote input/capture sessions are stopped.
