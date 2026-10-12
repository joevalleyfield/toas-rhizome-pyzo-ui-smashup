# macOS CI reproduction and local replay

## Status

Completed by Engineer, 2026-10-12. Compiled as Project Manager from Journal objective reproduce-macos-ci-acceptance.

## Objective

Investigate the hosted macOS workspace-close PID assertion and establish an isolated, repeatable local replay of the existing GitHub workflow.

## Acceptance Criteria

- Record baseline/diagnostic evidence and identify whether the failure is reproduced or remains unproven.
- Use main commit a9946e65 and manifest dependency/runtime pins in a fresh checkout.
- Replay bootstrap process controls, unit tests and live tests in CI order and retain logs/XML.
- Compare hosted artifact/runtime/environment with the local replay and record all remaining differences.
- Supply a reusable local replay entry point and short setup/reproduction documentation.
- Preserve original acceptance assertions/deadlines; do not claim complete Windows/Linux or Stage 7 acceptance.

## Allowed Write Surfaces

This isolated checkout's `scripts/`, `docs/`, task 042, ignored `.platform/` state and scratch diagnostic/evidence artifacts. Application code, Windows-specific code, OS installation and existing user data are outside the initial investigation scope. A behavior repair requires its own evidence-bounded proposal.

## Evidence Required

Exact source/runtime identities, workflow commands, retained baseline and replay logs, environment comparison, assertions for any diagnosis, and completion disposition.

## Completion Evidence

- [Investigation and raw evidence](../../docs/evidence/macos-ci-replay-2026-10-12/README.md): six unchanged local replays pass; observation passes; a synthetic 250 ms PID delay reproduces the assertion. Historical hosted cause remains unproven because its PID values were omitted.
- Fresh local build: bootstrap 6 passed/1 skipped; units 731 passed/30 skipped/2 warnings; all 27 live controls passed in 158.231s.
- Exact hosted wheel: same bootstrap and unit counts; all 27 live controls passed in 157.994s. All 61 captured package versions match.
- [Reusable replay](../../scripts/replay_macos_ci.py) and [local guide](../../docs/macos-ci-replay.md) record environment differences and detect command drift. Revision-pin checks and workflow rejection were verified separately.
- Application/probe behavior, workflow and deadlines are unchanged; pending-PID handling is an identified follow-up, not a completed repair. Windows work and task 041 remain separate and open.
- Exact macOS 15 OS/framework/hardware parity and visible native acceptance were not performed.
