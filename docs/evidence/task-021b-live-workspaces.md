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

## 021b1 — independent real-Qt projections (complete)

Pyzo revision `873b0101` adds `WorkspaceRuntimeCatalog`, which constructs and
disposes multiple runtime-owned backend/model pairs while passing the same
shared authorities to each runtime. The real-Qt regression constructs two
`QtAdsPeerFrameBackend` instances, registers one editor pane in each, renders
both floating frames simultaneously, verifies distinct native windows and
shared-service identity, then closes panes before removing the workspaces.

The focused runtime and real-Qt tests pass `4 passed`. This proves independent
projection ownership, but not yet Pyzo editor routing, shared live document
editing, or workspace-addressed activation; those remain the next 021b slice.

## 021b2 — shared live document routing (complete)

Pyzo revision `60b49ecb` extends the real-Qt fixture so each runtime owns an
actual editor dock. Both views bind to the same `DocumentResourceRegistry`:
editing in either runtime projects text and dirty state to the other, Undo and
Redo use one history, and the peer cursor remains view-local. Teardown closes
panes before removing workspaces, preserving the coordinator invariant.

The focused runtime/projection suite passes `5 passed`. Workspace-addressed
activation, close negotiation, retained reopen, and cross-workspace shell
refusal remain the final 021b routing slice.

## 021b3 — shell ownership refusal (complete)

The root coordinator change makes cross-workspace shell transfer explicitly
unsupported before any source or target mutation. The coordinator regression
now passes `16 passed`, including unchanged layouts and ownership after a
refused shell transfer. Shell execution remains workspace-local; editor-pane
transfer remains available only through the existing transactional capability
path.

The remaining 021b work is explicit workspace-addressed activation and close/
retained-reopen routing in the live Pyzo controller.
