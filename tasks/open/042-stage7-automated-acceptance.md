# Stage 7 automated acceptance stabilization

In progress, 2026-10-12. Start from merged main a9946e6; preserve assertions and
deadlines. Original CI: https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38292168062.

Windows reproduced with real DOS-path alias: long temp path passes; short path
stalls at wait-affinity-seed, and then release after partial canonicalization.
Canonicalize and normcase every cwd identity comparison. Dependency draft PR:
https://github.com/joevalleyfield/pyzo/pull/2. Pinned source 7d7a791fc406e5c1ed7960a1e0f9e95e72557b5a.

Linux Run Cell and macOS PID failures are reproduced locally by delaying actual
kernel evaluations to 0.3s. Old result_or_cancel(0.2) yields None and trips the
original assertion. Keep pending futures across retries, distinguish pending from
completed values, scope cached completions to phase/context/epoch, and retry
not-yet-defined names. Assertions and 0.2/phase/external deadlines stay unchanged.
Native Linux/macOS confirmation must come from CI, not local Windows results.

Focused short-path live replay: 3 passed, 40.30s. Old delayed controls fail; fixed
real delayed Run variants and close pass in 10.047s/7.281s. Coordinated units:
723 passed, 42 skipped, 2 warnings, 34.96s. Audit retains all 724 identities and
classifications; only the reviewed smoke scope hashes changed. Evidence:
docs/evidence/stage7-acceptance-2026-10-12.

Next: native three-platform CI replay, diagnose subsequent fail-fast failures
without relaxing checks, then remaining task 041 physical coverage: mixed DPI,
monitor reconnect, border resize, Explorer file delivery and pane/tab dragging.
The prior unchanged upstream Windows restart control remains a known distinct gap.

Native first repair CI: Windows passes reported cwd smoke and stops at pristine
restart (25 passed); Linux passes Run Cell then fails fresh assignment evaluation
(13 passed); macOS passes PID/close then catches late debugger quit callbacks
(20 passed). Additional repairs retain assertions/deadlines, label the post-move
query separately and move once; skip checkpoint/affiliation during committed exit
and retire broker before closing shell. Revised pin: 737aa0b8a0fa766fdac83a134496b0cfa52d500c.
Revised units 728 passed/42 skipped/2 warnings; assignment native/delayed local
controls pass, ten lifecycle regressions and five geometry/session regressions pass.
Mixed DPI exposed system-awareness startup calls; Qt defaults are now retained,
with actual DPR 2.0/1.5 observed after restart. The user authorizes leaving the
portrait display at 150% in the new arrangement. Physical reconnect is pending
user disconnect; other physical work proceeds with independent checks.

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

Reconnect completed, 2026-10-12: observer confirms primary DPR 2.0 and portrait
DPR 1.5. B returns to LS27A70 at reachable geometry [4430,-1279,417,661]; both
owners retain the identical shared dirty document and view identities, and no
observer errors appear. Native B File menu opens and all eight menus remain
available. Clean native Quit confirms termination of the test-owned shell;
about-to-quit reports no errors and launch supervisor exits zero. Fixture is now
closed. User's 150% portrait / 200% primary configuration remains in place.
This completes the requested mixed-DPI/reconnect/resize/Explorer/pane/tab physical
checks; resize was verified through native System/Size, not the unsuccessful
border-drag attempt. OS file-association launch was not configured or claimed.

2026-10-12 Windows restart follow-on: native debugger identifies Shiboken wrapper
cleanup during CRT DLL shutdown. Raw pristine source still crashes; disposing
its already-closed main window before the same actual os.execv succeeds. The
compatibility harness installs an explicit Windows/vanilla os.exec audit hook,
requiring committed/hidden/live window and verifying Qt invalidation. This is
a cleanup-assisted pristine-source control, not a claim that raw upstream restart
is repaired. All 342 exported baseline files remain byte-identical. Original
assertions, real successor and deadlines stay intact; no peer/legacy production
restart change. Focused guard + full compatibility matrix: 7 passed (81.81s).
Full units: 732 passed/42 skipped/2 warnings (35.47s); complete live run pending.
Evidence: docs/evidence/stage7-restart-2026-10-12.

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
