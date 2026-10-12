# Hosted macOS timing experiment

## Status

Completed by Engineer, 2026-10-12. Compiled as Project Manager from Journal objective test-hosted-macos-timing.

## Objective

Run the close and debugger controls on the actual GitHub macOS runner with resource and query observations.

## Acceptance Criteria

- Record CPU count, memory/load, source/runtime identities and all test outcomes on the hosted runner.
- Repeat the unchanged close/debugger acceptance controls and run observation-only probe launches.
- Preserve assertion thresholds, fixture ownership, phase/external deadlines and failure visibility.
- Retain logs/XML and wait for actual hosted results. Distinguish resource observations from causal hardware claims.

## Allowed Write Surfaces

New macOS diagnostic workflow, test-owned experiment/observation scripts, docs/evidence, task 043 and PR #3 metadata. Application code, original controls, Windows-specific repairs and merges are outside scope.

## Required Completion Evidence

Exact pushed revision, hosted run/job identity, resource snapshot, every repeated-control result, observed query states/timings and bounded interpretation.

## Completion Evidence

- [Actual hosted results and raw evidence](../../docs/evidence/hosted-macos-timing-2026-10-12/README.md), run 38316386127, job 115033902441, tested SHA 0976e108667365eda2d21908bd1617c2c1ab51e9.
- Runner reports VirtualMac2,1, three virtual M1 CPUs and 7 GiB memory, with high initial load averages. These observations do not prove a causal hardware explanation.
- Three unchanged rounds: close fails all three with retired-workspace callback errors; debugger passes two and fails one. Both observed probes fail on retained callback errors.
- All 27 observed queries, including PID reads, complete successfully. No PID timeout reproduced in this run. Deleted-shell callback also reproduced locally under observation.
- Build succeeds; experiment returns nonzero and preserves every failure. No original probe, application code, assertion or deadline was changed.
- CPU-affinity/hardware emulation, stress injection and application repairs were not performed. Local generated-runtime hidden plugin flags remain an observed adjacent issue with unknown cause.
