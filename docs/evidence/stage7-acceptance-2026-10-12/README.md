# Stage 7 post-merge acceptance — 2026-10-12

Original CI run: https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38292168062
Build/bootstrap controls and units passed on Windows, Linux and macOS; fail-fast
live failures were Windows wait-affinity-seed, Linux Run Cell negative assertion,
and macOS distinct integer PID assertion. Excerpts retain the original failures.

Windows: actual NTFS long/DOS-short temporary-directory pair reproduces the
reported phase: long passes, short stalls with both kernel identities correct.
All cwd comparisons now canonicalize and normcase both sides, including release.
The corrected short-path smoke, Run variants and workspace close pass together:
3 tests, 40.30s. Original smoke/phase/external deadlines and assertions stay intact.

Evaluation: the old result_or_cancel(0.2) returns None for a delayed request.
Injecting a real 0.3s kernel evaluation reproduces Run Cell's false assertion and
workspace close's PID assertion with that old behavior. A pending-aware poller
retains each request and throws a distinct pending signal until it completes.
The guard retries the same phase under its original deadline. Completed values
reach the unchanged assertions; actual bad values remain failures. Completed
name-not-defined results are retried, and context/epoch/phase scope prevents reuse
across kernel replacement. Corrected delayed runs pass in 10.047s and 7.281s.
This is a local real-kernel reproduction, not native Linux/macOS confirmation.

Units: 723 passed, 42 skipped, 2 warnings, 34.96s. Four focused unit regressions
pass: actual DOS-alias smoke release, delayed False, delayed integer/distinct PIDs
and bad PID rejection, plus name-not-defined retry. Native three-platform CI
confirmation is pending. Physical task 041 remains separately open.

## First native confirmation and follow-on repairs

Run 38308927592 passes the original Run Cell, close/PID and Windows cwd controls.
Windows reaches the known pristine restart failure (25 live controls passed).
Linux stops later at fresh post-move assignment response (13 passed); macOS at
late debugger teardown callbacks (20 passed). Failure excerpts are retained.
Assignment's late reply gets a distinct label; the layout move is performed once
before waiting, so neither a pre-move cached value nor repeated topology mutation
can satisfy the test. Actual delayed late evaluation reproduces the old failure;
corrected assignment passes normally in 7.421s and delayed in 8.359s.

The macOS checkpoint accessed disposed runtimes after committed quit. Checkpoint
and affiliation callbacks now ignore exit-in-progress; cancellation resumes them.
Committed shell close retires its broker identity before flushing/closing context,
preventing queued close events from decorating a Qt-deleted shell. Ten focused
lifecycle regressions pass. Revised units: 728 passed, 42 skipped, 2 warnings,
78.29s. Native follow-on CI confirmation remains pending.

Physical mixed DPI also reproduced startup forcing system DPI awareness (1),
then a rejected per-monitor API call (HRESULT -2147024891). Qt now selects native
per-monitor awareness itself. Its isolated startup regression passes; physical
DPR now reports 2.0/1.5. Geometry recovery relocates inaccessible restored title
bars after monitor/DPI coordinate changes, while reachable geometry is preserved.
Five focused session/geometry tests pass. See sibling stage7-physical evidence.

Second native replay (38311726531) catches stale completed evaluations during
assignment retirement on Windows/macOS (13 passed), and a timed-out direct smoke
evaluation on Linux (11 passed). Shared pending evaluation now covers the smoke
and all coordinated probes; completed results clear after a successful tick while
pending retries retain their batch. Assertions and deadlines remain unchanged.
Current dependency pin: da26a6c7c07e28d947f193215368e3723065a684. Nine focused
polling/audit/DOS-path/DPI checks pass locally (18.35s). Local assignment and failure
injection pass, but peer smoke reaches its original 10-second deadline; the delayed
debug-local control reaches value 41 then times out later. These timing failures
remain unresolved and are retained, rather than recorded as acceptance passes.

Third native replay 38314348252: macOS all 27 live controls pass (250.95s).
Windows passes 25 then fails the unchanged pristine os.execv restart parent
(access violation, 4294967295). Linux passes 21 then catches a find-bar auto-hide
timer accessing a disposed runtime after tools restore. Runtime disposal now
retires both find timers before native backend close and rejects queued auto-hide
callbacks; the same retirement applies when removing an editor host. Isolated
callback regression, runtime tests, context audit and real tools/restore replay:
9 passed in 28.16s. No assertions/deadlines changed. New pin:
803afaf3f952bd58e7b29df22435e721cb6123e8. Native confirmation pending.

Current complete units: 730 passed, 42 skipped, 2 warnings in 37.02s.

Final local peer/legacy smoke replay passes (13.484s/9.516s subprocess elapsed,
original internal ten-second smoke limit unchanged). Its companion fallback
selection was initially skipped because compatibility opt-in was omitted; the
separate correctly enabled pristine save/quit migration/fallback replay passes
in 23.61s. This does not remove or replace the pristine restart failure. Strict
bootstrap reuse validates a clean clone at pin 803afaf3. Historical patch applies
to original c956237 and matches all 21 modified pinned files (LF normalized).
Earlier timing-failure evidence remains retained; one pass does not establish
absence of timing variation. Fourth native replay: 38316091949, ccb1457.

Fourth native Linux replay stops earlier at provenance's negative boolean check:
its remaining direct result_or_cancel(0.2) yields a failed assertion (15 passed).
Provenance now uses the same pending poller and clears successful tick values.
Local normal provenance passes (6.547s). Injecting a real 0.3s evaluation delay
reproduces old helper returning None at the unchanged False assertion; the old
probe reports Traceback although its exit code is zero (the existing harness
rejects that traceback). An initial diagnostic incorrectly expected exit 1 and
is retained. Fixed delayed provenance reaches False and completes with no
traceback under original 12-second phase/35-second external deadlines. All 724
context identities and classifications remain unchanged.

Fifth native replay 38316926851 at coordinator 66a87f1/dependency 803afaf3:
Linux all 27 live controls pass (259.18s); macOS all 27 pass (244.77s).
Both complete jobs succeed, including build, bootstrap controls and units.
Windows result pending at time of this entry; keep pristine restart separate.
Physical reconnect remains pending user hardware action, with fixture left open.

Final Windows result from the same fifth replay: 25 passed, 1 failed (256.11s).
Only failure is the unchanged pristine upstream restart parent access violation
at os.execv (4294967295); successor state/kernel execution/quit all verify.
Original three reported failures and patched application controls pass. Stage 7
is not marked all-green because this original assertion remains required. Linux
and macOS complete jobs pass. Current production/test source is validated by
66a87f1; subsequent receipt-only commit does not change that source.
Monitor reconnect remains awaiting the user; task-owned fixture stays open,
with one screen and no observer errors. No claim of completed physical reconnect.
