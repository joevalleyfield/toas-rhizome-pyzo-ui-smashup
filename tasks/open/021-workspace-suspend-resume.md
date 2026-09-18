# 021: Suspend and resume workspace participation

## Status

REVIEW_REQUIRED — owner unclaimed; intended executor Luna. Luna reported the
single-runtime stop boundary on 2026-09-18, with no implementation changes.
The [prerequisite review](../021-runtime-prerequisites.md) resolves the planning
question with 021a → 021b → 021c; this task remains gated until they pass.
Dependencies: 020 and 021a–021c complete and committed.

This is a bounded Experiment 014 follow-up, not a new product phase. Read and
follow [the batch execution contract](../local-retention-batch.md), which defines
scope, isolation, commit authority, and completion evidence for every task.

## Outcome

Connect workspace unload/reload to the shared retained document authority, with conservative live-shell closure.

## Read before editing

Under `spikes/peer_frames/` unless a different path is specified: `workspace_lifecycle.py`, `workspace_coordinator.py`, `workspace_session.py`, `workspace_persistence.py`, Pyzo workspace persistence/startup and application lifecycle services.
Also read the normative [September amendment](../../docs/local-workspace-scope-2026-09-06.md)
and predecessor completion evidence.

## Allowed writes

Those root workspace modules and matching tests; Pyzo workspace capture/restore/close sections of `main.py`, `applicationController.py`, `_start.py`, and matching nested tests. Minimal shell-close adapter changes in `shellGroups.py` if needed.
This task's status/evidence and `docs/evidence/task-021-local-retention.md`
are also allowed. Other writes require a bounded handback, not inferred scope.

## Decisions and boundaries

- A closed workspace stores context and references, never an authoritative private document-text snapshot.
- Reuse 021c's runtime factory, persistence and named create/open/activate commands. Add workspace close and connect closed-workspace reopen to suspend/resume through the coordinator; preserve optional roots and avoid a new workspace-management UI framework.
- A's reopen uses the latest retained document after B edits while A is closed. Restore only the application's recorded open set on normal restart.
- Closing a workspace preflights shell termination confirmation, makes editing state durable, then terminates/detaches. Cancelled confirmation or retention failure occurs before destructive work.
- Cross-workspace shell movement must be rejected before backend movement; do not add transitional or zombie state. Buffer-view transfer remains permitted.
- Source file contents never change as a side effect of workspace closure or reopening.

## Acceptance

- Real A/B shared document: close A, edit/undo in B, restart with B only, reopen A; identity and latest unsaved text/history agree.
- Close both workspaces, restart, explicitly reopen A without B; retained state is still available.
- Untitled buffers, independent view positions, nested/optional roots, failed workspace restore, and cancelled close.
- Live/debugging shells: explicit termination warning, cancel preserves workspace, persistence failure prevents termination.
- Rejected cross-workspace shell drag leaves both model and Qt layout unchanged.

## Stop boundary

The originally identified missing runtime seam is assigned to 021a–021c. Do not
start this task until their live Qt and restart evidence passes. Report any new
missing seam to Astra. Do not emulate multiple workspaces with renamed global
state or create a new framework.
Use REVIEW_REQUIRED or BLOCKED with the smallest reproduction and a concrete
question. Do not mark partial implementation complete or enable dependent work.

## Completion evidence

Pending. Record changed behavior, meaningful before/after assertions, commands,
results, remaining limits, and separate root/Pyzo revisions under the batch
contract. Move to COMPLETE only when all acceptance criteria are satisfied.
