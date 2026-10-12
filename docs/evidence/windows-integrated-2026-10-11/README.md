# Integrated Windows review replay — 2026-10-11

Published Pyzo pin: 93d3f97f66d00cd4964a14a44c588cc3be403935. Strict bootstrap checkout accepted the clean
verification clone at this published pin. The historical patch reproduces all
thirteen changed files against c956237. Setup rebuilt the pinned QtAds wheel
successfully during integration; the QtAds pins and ABI did not change.

Coordinated units: **719 passed, 42 skipped, 2 warnings**, 53.48s.
Coordinated live: **25 passed, 2 failed**, 412.02s. Bootstrap returns nonzero.
Ordinary peer and legacy smoke, Run variants, retention, ingress, assignment,
debugger, tools, patched restart and 1/4/8-workspace scale pass together.
Eight-workspace restore: **22.328s**, unchanged 60-second deadline.

Failures: the unchanged pristine upstream native Windows os.execv restart;
and the injected-failure smoke control timed out during initialization before
reaching its injected callback. The independent pristine save/quit migration
control passes. Neither failure is skipped or marked accepted.

focus-guard-live.* records the earlier two timing failures after focus gating.
linear-shell-registration-live.log records a repaired eight-workspace restore
(42.875s) and the remaining smoke timing failure. profile-summary.txt is a
*diagnostic*, not acceptance: startup action registration caused 276,039
shell enabled-state evaluations. Cumulative times include Qt re-entry/thread
interaction; call counts identified the repeated full-census refresh.
The kernel-overlap experiment was reverted; final source retains smoke sequencing.

Physical evidence is in ../windows-native-desktop-2026-10-11. Multi-monitor/DPI,
OS association/Explorer drop, all tab positions and native cross-frame dragging
remain open. Raw logs/XML intentionally retain diagnostic whitespace.

Isolated injected-failure control replay: **1 passed**, 19.41s, exercising both
timeout and exception injections with nonzero exits. This demonstrates the
failure protocol works on unchanged source, but does not erase the coordinated
startup timeout. Treat that timeout as intermittent and retain both results.
