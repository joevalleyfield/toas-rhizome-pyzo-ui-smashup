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
requirements and risk follow-up feed Task 014, which is the staged concurrent-
workspace implementation plan. Task 014 Stage 1 is the current queue head; its
seven stages are independent acceptance and commit boundaries.
