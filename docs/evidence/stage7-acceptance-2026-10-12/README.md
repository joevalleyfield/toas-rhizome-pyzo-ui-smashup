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
