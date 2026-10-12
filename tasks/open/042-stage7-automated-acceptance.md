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
