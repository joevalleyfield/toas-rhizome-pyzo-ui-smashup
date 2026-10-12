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
