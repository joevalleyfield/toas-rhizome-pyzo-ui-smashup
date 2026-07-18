# Experiment 005: Integrated feasibility decision

## Status

Complete on 2026-07-17. The fresh contract/backend suite, real peer-mode Pyzo
workflow, and legacy control passed. Pyzo is viable with bounded maintained
forks and the completion gates recorded in
[the integrated feasibility decision](../../docs/evidence/experiment-005-feasibility-decision.md).
The task remains under `tasks/open/` because this repository preserves numbered
experiment artifacts in place while the execution checklist carries queue
state.

## Objective

Run the complete acceptance workflow and decide whether Pyzo is a viable
foundation for a longer-lived fork and later toas/rhizome window integrations.

## Dependencies

- Experiment 004 verifies the complete debugger workflow.
- Experiment 010 supplies the requirement-to-owner and fork-boundary evidence.

## Acceptance criteria

- The workflow in REQUIREMENTS.md is demonstrated end to end.
- Peer-frame and pane-lifecycle contract scenarios pass against the selected
  backend and Pyzo integration.
- Dependency revisions and local modifications are recorded.
- Windows/Linux portability risks are identified and bounded.
- The Pyzo foundation receives a clear viable, viable-with-conditions, or not-
  viable assessment.
- Follow-up integration candidates are recorded without beginning toas or
  rhizome UI work prematurely.

## Allowed write surface

- Root-level feasibility and integration notes.
- The local Pyzo and docking project surfaces only for fixes needed to complete
  the acceptance workflow.
- This task artifact for the decision and evidence.

## Completion evidence

Record the final demonstration procedure, revision map, portability assessment,
decision, and bounded follow-up candidates.

Completed by the linked evidence document. The final replay passed 147 tests
with three expected stock-wheel capability skips, the unrestricted legacy
control, and the real peer-mode Run/live-debug/post-mortem/multi-kernel workflow.
