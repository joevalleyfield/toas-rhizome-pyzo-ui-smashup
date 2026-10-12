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
