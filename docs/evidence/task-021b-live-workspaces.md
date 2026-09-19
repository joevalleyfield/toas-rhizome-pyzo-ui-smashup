# 021b progress evidence: two live workspace runtimes

Date: 2026-09-18
Status: IN_PROGRESS

021a is complete. This task is being executed in bounded slices, beginning
with explicit runtime ownership and coordinator construction before adding a
second visible Qt workspace.

## Slice plan

- 021b0: construct two runtime-owned workspace services with distinct owner
  identity and shared document/undo authority.
- 021b1: attach two real Qt projections and route activation and view creation
  by explicit workspace owner.
- 021b2: exercise close, retained reopen, and cross-workspace refusal while
  preserving 021a startup/teardown behavior.

No durable multi-workspace availability is claimed until 021c persistence and
021 itself are complete.

## 021b0 — runtime ownership (complete)

Pyzo revision `fd5a1fb8` adds explicit shared-service references to each
`WorkspaceRuntime`. Runtime disposal still clears only its native host maps and
backend; shared document/undo authorities are not disposed with a workspace.
The focused Pyzo runtime tests pass `3 passed`, including two distinct runtime
backends/models registered with the root coordinator and sharing the same
document and undo authorities. The existing coordinator suite passes
`15 passed`.

The next slice will attach a second runtime to real Qt projections and route
workspace activation explicitly; this slice does not claim that live UI
capability yet.
