# Task queue

Tasks in `open/` are ordered experiments derived from [PLAN.md](../PLAN.md).
An Engineer claims one task at a time, records evidence in the task artifact,
and moves completed work to `closed/` when the repository queue protocol is
established.

The architecture-boundary sequence is:

1. `006-peer-frame-contract.md`
2. `007-qtads-peer-frame-adapter.md`
3. `008-pyzo-pane-projection.md` and `009-pane-lifecycle.md`
4. `004-core-tools-and-debugger.md`
5. `010-fork-boundary.md`
6. `005-feasibility-decision.md`

Tasks 008 and 009 may proceed in either order after 007, but both must complete
before the end-to-end debugger and feasibility decisions.
