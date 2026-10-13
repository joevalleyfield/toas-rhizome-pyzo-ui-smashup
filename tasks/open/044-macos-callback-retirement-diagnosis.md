# macOS callback retirement diagnosis

## Status

Completed by Engineer, 2026-10-12. Compiled as Project Manager from Journal objective diagnose-macos-callback-retirement.

## Objective

Turn actual hosted teardown failures into local state/assertion evidence and a bounded repair proposal.

## Acceptance Criteria

- Trace both hosted failure paths in unchanged pinned Pyzo code.
- Enumerate callback lifetime states and executable invariants, including canceled exits and normal unexpected disconnects.
- Execute deterministic diagnostics; preserve results and classify unsupported states explicitly.
- Document repair scope and verification plan before the state-assertion skill confirmation gate.

## Allowed Write Surfaces

Task 044 and diagnosis documentation/evidence only. Application code, acceptance controls, deadlines, dependency pins, Windows work and merges are excluded until separately confirmed after the state gate.

## Required Completion Evidence

Source identities, executable diagnostic commands/results, state-to-code coverage map, concrete proposal and remaining validation gaps.

## Completion Evidence

- [Pre-edit diagnosis](../../docs/evidence/macos-callback-retirement-2026-10-12/README.md) maps callback and exit states to executable assertions and source paths.
- 16 callback combinations: ten invariant passes/six gaps; 16 real coordinator exit boundaries pass; six checkpoint edge controls pass their expected outcomes; actual committed close and real queued-event dispatch expose retirement gaps.
- Real Qt deletion reproduces the shell error; retired catalog reproduces the checkpoint error without artificial load. Existing lifecycle suite: 18 passed.
- No application source/control/deadline changes in this task. Source hashes and exact clean dependency revision retained.
- User explicitly confirmed both lifetime fixes after reviewing the gate on 2026-10-12. Implementation proceeds under a separate repair task.
- Full/hosted repair verification and visible desktop tests deferred to implementation; no hardware causality or PID-timeout repair claimed.
