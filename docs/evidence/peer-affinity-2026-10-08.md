# Peer affinity smoke acceptance — 2026-10-08

[035](../../tasks/open/035-peer-affinity-smoke-acceptance.md) is accepted. The full
peer startup smoke now passes Run, live debug, postmortem and real two-kernel
affinity. Timeout/exception paths terminate test-owned resources and exit 1,
without printing a completion marker. Production routing remains unchanged.

Root implementation `d721cfe1c2a0abdf54a81aa604ed75fa40d0624c`, parent
`11f007897313810eb7a1abf32815ccdf5bcfde14`; Pyzo implementation
`db2475a7257115d3b50957c6f8698416ec53c2fc`, parent
`0e334f57de142cf4deeee4dd43b5b1453b9ad6f4`. Both precede acceptance.
Native QtADS/binding and the pinned wheel are unchanged from 034. Same Python
3.12.13, PySide6/Qt 6.11.1 and IPython 9.17.1 runtime. Nothing pushed.

[Diagnostic](peer-affinity-2026-10-08/diagnostic.log): first kernel is
Ready/connected and resolves; second has a version but an empty state and is
correctly refused with NO_TARGET. The smoke sent its seed too early and then
waited forever for an identity that was never set. Both initial Run and affinity
seed gates now require version, Ready and a connection. They send once, then
observe results. No eligibility guard or provenance requirement is relaxed.

The Qt timeout/exception branches formerly called qApp.exit(1), while `start()`
ignored Qt's return and only checked `_test_exit_code`. Both branches now use
the existing test abort path: stop timer/callback dispatch, clean owned kernels
and server, set `_test_exit_code=1`, exit. The ten-second peer deadline remains.

56 readiness combinations test dispatch effects on both shells, including
version, status and connection variations. Held-phase and exception injection
are implemented only in the test-owned probe. The harness permits traceback
output only when explicitly requested with an expected nonzero exit; ordinary
positive controls remain strict.

Validation:

- [Coordinating/Pyzo suite](peer-affinity-2026-10-08/coordinated.log): 647 passed,
  348 subtests, 21 skipped (20 opt-in controls and stock capability case), two
  existing Qt deprecations.
- [Smoke success/failure controls](peer-affinity-2026-10-08/smoke-controls.log):
  peer affinity and legacy pass; injected timeout and exception exit exactly 1
  and omit APPLICATION SMOKE COMPLETE.
- [All live controls](peer-affinity-2026-10-08/live.log): 20 passed in 93.21s,
  including the native restore regression and all existing Run/debug/retention/
  recovery/closure/tool/ingress controls.
- [Ruff F](peer-affinity-2026-10-08/source-checks.log) passes. Changed sources
  compile and have no trailing whitespace.

[034](native-restore-2026-10-07.md) correctly recorded the previously hidden
peer affinity warning; this slice resolves that warning and its reporting gap.
Stage 7 scale/final census and remaining physical/platform/vanilla/integrated
compatibility gates remain separate. Read-only census inspection exposed
owner-sensitive Replace All, help-finish, file-drop and local tool-open paths;
those enter the authorized next census slice, not this smoke repair.

Reproduce with `RUN_LOCAL_EXECUTION_ACCEPTANCE=1 PYTHONPATH=.` and the configured
`.codex-local/bin/uvt run --offline --python 3.12 --with pytest python -m pytest
spikes/peer_frames/test_local_execution_acceptance.py -k application_smoke -q -s`.
Probes own temporary appdata and process groups; no user command server is used.
