# Task queue

Tasks in `open/` are ordered experiments derived from [PLAN.md](../PLAN.md).
An Engineer claims one task at a time, records evidence in the task artifact,
and moves completed work to `closed/` when the repository queue protocol is
established.

The architecture-boundary sequence is:

1. `006-peer-frame-contract.md`
2. `007-qtads-peer-frame-adapter.md`
3. `011-per-group-tab-edges.md`
4. `008-pyzo-pane-projection.md` and `009-pane-lifecycle.md`
5. `004-core-tools-and-debugger.md`
6. `010-fork-boundary.md`
7. `005-feasibility-decision.md`
8. `012-hidden-main-removal.md`

Task 011 is the recommended next layout experiment after 007. The first slice
of 008 may inform it, but deeper application-chrome work should wait for its
fork boundary. Tasks 008 and 009 may otherwise proceed in either order; both
must complete before the end-to-end debugger and feasibility decisions.

After the feasibility decision, Task 012 is the selected architecture cleanup.
It removes the temporary hidden Pyzo application host before any toas/rhizome
integration begins.

Task 013 audits current state ownership after hidden-main removal. Its accepted
requirements and risk follow-up feed Task 014, the seven-stage concurrent-
workspace implementation inside overall Plan Phase 10. Task 014's first three
stages retain their dated July acceptance. Revised retention is accepted in the
[2026-10-04 integration review](../docs/evidence/retention-integration-2026-10-04.md):
015–022 implemented the retained-document workflow; 023 reconciled the review
gates; 024 added explicit legacy selection; 025 corrected shared-view lifecycle,
restore authority and native close routing.

The current queue head is [026: live workspace Execute Selection](open/026-live-workspace-execute-selection.md).
Later Stage 4 work covers explicit assignments, broken targets, all Run variants
and complete provenance. Stages 5–7 cover ordinary debugging, contextual tools
and integrated compatibility. File Move/Fork UX remains a separate local slice.
The [September amendment](../docs/local-workspace-scope-2026-09-06.md) remains
normative: shell transfer is visibly refused; live shell migration, zombies,
portable synchronization and broad TOAS/Rhizome integration are deferred.

[The execution checklist](../EXECUTION_CHECKLIST.md) owns the mutable order.
Tasks stay at stable paths with explicit status and commit/evidence links.
The [retention batch](local-retention-batch.md) and
[September runtime prerequisite review](021-runtime-prerequisites.md) retain
historical dispatch/dependency details. No pending task is inferred complete
from a model test or a passing retention harness.
