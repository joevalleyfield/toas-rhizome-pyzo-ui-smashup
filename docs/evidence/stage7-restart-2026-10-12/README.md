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
