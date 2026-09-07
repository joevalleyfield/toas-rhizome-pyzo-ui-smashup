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
implementation stages were accepted under the July contract. The current queue
head is retention/lifecycle and migration reconciliation under the
[2026-09-06 local workspace amendment](../docs/local-workspace-scope-2026-09-06.md),
followed by the real-editor retention proof and resumed Stage 4 execution routing.
Shell migration and zombie workspaces are deferred. The execution checklist owns
the mutable order; every accepted slice remains an independent commit boundary.

The executable follow-up is [local retention tasks 015–022](local-retention-batch.md).
Only 015 is READY; later tasks have explicit prerequisites and the 018 real-editor
undo proof requires Astra acceptance before live integration. Each task is scoped
for Luna with allowed writes, state/failure assertions, and handback conditions.
[Astra's self-handoff](../docs/handoffs/2026-09-06-local-retention-review.md) owns
the intermediate architecture gate and final integration review. Task files stay
at stable paths and record READY/WAITING/IN_PROGRESS/REVIEW_REQUIRED/BLOCKED/COMPLETE
status so links survive this batch. Completion does not imply Stage 4 acceptance.
