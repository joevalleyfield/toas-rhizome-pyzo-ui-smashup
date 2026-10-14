# Windows pristine-source restart control, 2026-10-12

The preceding Stage 7 CI run 38316926851 passes 25 Windows live controls, then
fails pristine-source restart's original zero-exit assertion. Its real successor
restores state, executes code and quits, but the original process reports an
access violation and status 4294967295. Baseline remains
26c2c32778dddf8fca3c1a44112941b22f075264; all 342 exported files remain byte-identical
after these diagnostics (baseline-integrity.txt).

Minimal Python exec succeeds with no watchdog, an active watchdog, a cancelled
watchdog, and a worker thread. Minimal Qt application/widget/text/font/callback
exec also succeeds. Full pristine profile comparisons reproduce the crash with
both offscreen and native Windows backends. Cancelling the watchdog, joining all
remaining Python workers, removing application fonts, or disposing only the
probe timer does not repair it. Disposing the already-closed main window or the
application before the same real os.execv call makes parent and successor succeed.

The installed native debugger stops just before real exec, then captures the
first cleanup exception. The stack includes Shiboken BindingManager destruction
under the Windows CRT on-exit table / DLL process shutdown, after warnings about
Qt thread storage destruction. Inner frame names without PDBs are approximate
export labels; do not use them as exact function attribution. Qt's pinned
[BindingManager destructor source](https://raw.githubusercontent.com/pyside/pyside-setup/6.11.1/sources/shiboken6/libshiboken/bindingmanager.cpp)
also shows wrapper invalidation when Python remains initialized. This supports
the diagnosis of Qt/Shiboken object cleanup during CRT/DLL exit, rather than a
failed successor launch or profile corruption.

The compatibility harness now installs a Windows-only audit hook for vanilla
mode's actual os.exec event. It requires a live window, committed close flag and
hidden window, then disposes that closed Qt graph and verifies invalidation.
It does not change upstream files, replace os.execv, rewrite arguments, substitute
a successor, change exit expectations, or extend deadlines. This is explicitly
a cleanup-assisted pristine-source control; raw unassisted Windows behavior
continues to fail and is retained here. Production peer/legacy restart remains
on its existing process handoff, and Linux/macOS receive no audit hook.

Two focused guard regressions verify cancellation/visibility/missing window and
failed deletion reject cleanup, while exec arguments remain untouched. All five
existing compatibility controls pass locally: together 7 passed in 81.81s.
Original PID/token, source byte/mtime, kernel execution, cancel, migration,
fallback and zero-exit assertions remain intact. Full unit phase after adding
the explicit cleanup receipt: 732 passed, 42 skipped, 2 warnings (35.47s).
Complete live/bootstrap and native three-platform replay are pending.

Diagnostic scripts are retained with their original paths in logs. To rerun a
raw comparison, point RESTART_DIAGNOSTIC_TARGET to raw-profile-probe.py, export
the recorded baseline, and supply isolated profile paths as in the logged
diagnostics. They are diagnostic variants, not acceptance replacements.

Complete local bootstrap.py test now exits zero: 732 unit checks passed, 42
skipped, 2 warnings (35.47s); all 27 live controls pass (340.95s). The vanilla
seed run records WINDOWS CLOSED-WINDOW EXEC CLEANUP, real successor restored
state/kernel execution/quit, and original zero-exit assertion. Compilation and
source whitespace checks pass. Native CI run 38325575192 is pending.

Native first cleanup candidate (38325575192, b4f2821): Windows complete job
succeeds, 745 units passed/29 skipped and all 27 live controls pass (277.32s);
macOS complete job succeeds, 742/32 and 27 live pass (221.67s). Linux fails
debugger seed's remaining direct timeout helper with a None PID (20 passed).
The remaining debugger, execution and tools eval helpers now share the pending
poller; no direct result_or_cancel(0.2) remains in these Qt probes. Debugger close
attempts and execution topology/disconnection actions run once while pending
replies retain their batch. Assertions, original phase and external deadlines
remain intact. Context census keeps all 724 identities and classifications.
Normal debugger/tools + shared regressions pass (9 checks, 37.51s); normal real
execution passes separately. Actual 0.3s PID and negative/late/moved/disconnected
queries reproduce old failures and complete with the revised helpers. The first
tools delay diagnostic omitted its required phase variable and yielded KeyError
for both variants; that setup error is retained and the corrected replay
reproduces old repeated None/phase timeout and completes with the fixed helper.
Native final replay pending.

Final polling-conversion units: 732 passed, 42 skipped, 2 warnings (35.15s).

Final automated acceptance accepted, 2026-10-12 (America/New_York). Source
e423978fe248ce1c9f0908f9b23e2a274e3d6997 / Pyzo
803afaf3f952bd58e7b29df22435e721cb6123e8 / QtADS
244157db5bdffdf9d250e58a6edf8ee6acfd3a61 / binding
764eb4a487abccb162dcbee1a8f0383916561e0e. Native CI 38327905266 succeeds on
all three platforms, including setup, bootstrap controls, units and live suites:
Windows 745 units/29 skipped and 27 live (289.68s); Linux 742/32 and 27 live
(256.15s); macOS 742/32 and 27 live (212.26s). Final local units 732/42/2 warnings
(35.15s); final current-source live replay all 27 passed (335.83s).
Windows pristine-source control is explicitly cleanup-assisted; raw CRT/Shiboken
shutdown failure remains retained and is not claimed fixed in upstream source.
All original assertions and deadlines remain, all 724 context identities and
classifications remain, and physical Windows requested checks are complete with
clean Quit. Subsequent receipt/checklist-only commit changes no tested source.
This completes task 042's automated stabilization scope; it does not infer whole
Experiment 014 / requirement-platform-matrix / File Move-Fork acceptance.
