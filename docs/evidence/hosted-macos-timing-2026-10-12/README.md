# Actual hosted macOS timing experiment — 2026-10-12

Tested revision: `0976e108667365eda2d21908bd1617c2c1ab51e9`.
[Hosted experiment run 38316386127](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38316386127),
job 115033902441, artifact 11776931266 (`macos-hosted-timing`).
The pinned runtime built successfully; the experiment deliberately returned
nonzero because it retained failed controls and observed exceptions.

## Reported hardware and resources

| Property | Hosted runner | Local observation |
| --- | --- | --- |
| Model | VirtualMac2,1 | Mac17,6 |
| CPU | Apple M1 (Virtual), 3 CPUs | Apple M5 Max, 18 CPUs |
| Memory | 7 GiB | 128 GiB |
| Initial available memory | 3,681,550,336 bytes | 62,319,820,800 bytes |
| Initial load averages (1/5/15 min) | 23.94 / 19.10 / 13.20 | 2.36 / 2.08 / 1.83 |

These are guest-reported resource observations, not measured CPU steal time or
proof that hardware alone caused a failure. The values are in `identity.json`
and per-control snapshots in `results.json`. Both runs use the same source pins;
runtime version is Python 3.12.13. Hosted interpreter reports Clang 22.1.3 and a
June build; local interpreter reports Clang 22.1.1 and a March build. OS remains
15.7.9 hosted versus 27.0.1 local. Hardware/scheduling is the current emphasis.

## Unchanged acceptance controls

| Round | Workspace close | Debugger and restart restore |
| --- | --- | --- |
| 1 | Fail: uncaught retired-workspace callback | Pass |
| 2 | Fail: uncaught retired-workspace callback | Pass |
| 3 | Fail: uncaught retired-workspace callback | Fail: uncaught retired-workspace callback |

Total: two passing and four failing original test cases. Their original PID,
retention, ownership, phase and external-deadline assertions were unchanged.
Each failed round returned 1; none exhausted the experiment's outer timeout.
The original debugger control can report a caught deleted-shell event while
its accepted completion assertions still pass. The observation experiment also
rejects caught event exceptions, so this signal is retained separately.

## Observed probes

- Close reaches `WORKSPACE CLOSE COMPLETE`, then emits
  `unknown workspace runtime` from `_checkpointPeerContext` →
  `contexts.apply_preferences` → runtime lookup. Observation is failed even
  though the process returns zero.
- Debugger reaches `WORKSPACE DEBUGGER COMPLETE` but emits
  `Internal C++ object (PythonShell) already deleted` in `_onConnectionClose`.
  Observation is failed even though the process returns zero.
- All 27 captured query requests completed successfully (Future status 4),
  including every captured PID request. Maximum measured wait was 0.213453s
  for close and 0.225774s for debugger. No observed request returned a timeout
  or canceled/error state. This run does not reproduce the earlier PID failure.

The local cached-runtime validation passed the unchanged close/debugger tests
and the observed close probe, but observation reproduced the same deleted-shell
callback during debugger teardown. A constrained virtual runner is therefore
not a necessary condition for that callback error. Query logging perturbs timing;
the three original-test repetitions provide the separate unchanged baseline.

## Earlier hosted PR run

[PR run 38309668061](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38309668061)
also passed the original close/PID boundary and failed later debugger teardown
with both deleted-shell and retired-workspace errors (20 live passes, one fail).
The latest evidence shifts immediate repair attention to callback retirement.
The historical 0.2-second PID-read fragility remains a separate demonstrated
test boundary; it is not the cause established by this experiment.

## Local environmental observation

The generated `.platform/environment` acquired macOS `hidden` flags on all
three platform plugin dylibs. Python could list/read them, but Qt's normal
directory listing excluded them, causing offscreen startup to abort. Clearing
those flags made startup pass immediately; the flags subsequently reappeared.
The source of the metadata changes was not established. This is recorded as
an adjacent local-environment issue, not attributed to the hosted runner or
the application. Actual hosted startup and runtime build passed.

## Disposition

Upstream experiment complete, failures preserved. No application repair or
deadline/assertion relaxation is included. Next repair candidates are retirement
of context checkpoint callbacks and broker-close observers before their owners
are disposed, with a separate state/assertion coverage gate. Task 041 and
Stage 7 remain open. No memory/CPU stress injection, CPU-affinity emulation or
hardware-causality proof was performed.

Raw logs, XML, identities and every result are retained under `hosted/` and
`local-observed/`.
