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

[026: live workspace Execute Selection](open/026-live-workspace-execute-selection.md)
is complete; [its evidence](../docs/evidence/workspace-selection-2026-10-04.md)
records the accepted bounded live slice.
[027: live Selection assignments](open/027-live-selection-assignments.md) is also
complete, including the checked chooser and broken-target correction.
[028: remaining workspace Run variants](open/028-live-workspace-run-variants.md)
is complete, including retained Main and native script save/restart policies.
[029: native request/result provenance](open/029-native-request-result-provenance.md)
is complete; [its evidence](../docs/evidence/native-provenance-2026-10-05.md)
accepts native provenance together with 026–028.
[030: real-kernel workspace closure](open/030-live-workspace-close-acceptance.md)
is complete; [its evidence](../docs/evidence/workspace-close-2026-10-05.md) supplies
the missing integrated closure proof and bounded repairs, correcting 029's broad
sign-off. Local Stage 4 is accepted through 026–030.
The current queue head is [014 Stage 5](open/014-concurrent-workspace-implementation.md#5-workspace-breakpoint-overlays-debugging-and-conservative-closure): durable breakpoint overlays,
debugger/session ownership, postmortem attribution and conservative closure.
Stages 6–7 cover contextual tools and integrated compatibility. File Move/Fork UX remains a separate local slice.
The [September amendment](../docs/local-workspace-scope-2026-09-06.md) remains
normative: shell transfer is visibly refused; live shell migration, zombies,
portable synchronization and broad TOAS/Rhizome integration are deferred.

[The execution checklist](../EXECUTION_CHECKLIST.md) owns the mutable order.
Tasks stay at stable paths with explicit status and commit/evidence links.
The [retention batch](local-retention-batch.md) and
[September runtime prerequisite review](021-runtime-prerequisites.md) retain
historical dispatch/dependency details. No pending task is inferred complete
from a model test or a passing retention harness.
