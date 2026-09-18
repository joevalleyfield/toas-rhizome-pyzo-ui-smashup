# 021a0: Reconcile runtime-owned frame chrome

## Status

READY — intended executor Luna. Dependency: 020 complete.
Follow the [prerequisite review](../021-runtime-prerequisites.md) and
[batch contract](../local-retention-batch.md).

## Outcome

Make status and command projection follow the owning runtime's authoritative
frame set during QtADS frame destruction, recreation, and deferred deletion.
The single-workspace clean editor lifecycle must not retain a stale projection
or miss a newly live frame.

## Allowed writes

Root `spikes/peer_frames/qtads_status.py`, `qtads_commands.py`, matching tests,
and the smallest Pyzo integration change in `deps/pyzo/pyzo/core/main.py` or
`workspaceRuntime.py` needed to pass the runtime's frame provider explicitly.
Evidence belongs at `docs/evidence/task-021a0-runtime-chrome.md`.

## Implementation contract

- Projectors reconcile against an explicit runtime frame provider or snapshot;
  they must not infer ownership from a second, independently timed QtADS list.
- Reconciliation is triggered after every committed topology change, including
  frame creation, committed close, deferred deletion, zero-frame recovery, and
  runtime disposal. The trigger is owner-bound and idempotent.
- Each trigger has a defined settled point: deferred Qt deletion is drained,
  the runtime frame snapshot is captured, reconciliation runs, and equality is
  asserted against that same snapshot before the operation is reported done.
- Removed frame IDs are forgotten, newly live frames are projected exactly
  once, and repeated reconciliation is idempotent.
- Status and command projections remain separate services but observe the same
  owner-bound frame set. No focus-driven rebinding or global singleton is
  introduced.
- Deferred Qt deletion, frame recreation, zero-frame recovery, and a failed
  projection leave no orphan projection or stale callback. Tests must verify
  actual widget/event-filter/callback cleanup, not only matching ID sets.

## Acceptance

- Real Qt frame recreation passes the existing clean editor lifecycle matrix
  with exact projected/live frame-ID equality and no callback traceback.
- Unit tests cover stale-only, new-only, replacement, empty, and repeated
  reconciliation states for both projectors.
- Existing retained-buffer, workspace-session, controller, shell, and pane
  movement smokes remain passing.

## Stop boundary

Do not extract the full workspace runtime, add a second workspace, or change
workspace persistence. If the owning frame provider cannot be passed without
rewriting QtADS integration, return the smallest seam and reproduction.

## Completion evidence

Record commands, isolated real-Qt output, root/Pyzo revisions, and the next
eligible task at the evidence path above.
