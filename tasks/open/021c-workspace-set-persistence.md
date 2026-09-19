# 021c: Persist and restore the live workspace set

## Status

COMPLETE — owner Codex; completed 2026-09-19. Dependency: 021b complete and
committed. Completion evidence is recorded at
[`docs/evidence/task-021c-workspace-persistence.md`](../../docs/evidence/task-021c-workspace-persistence.md).
Follow the [prerequisite review](../021-runtime-prerequisites.md) and
[batch contract](../local-retention-batch.md).

## Outcome

Capture/restore every remembered open workspace through the runtime factory.
Provide minimal named create/open/activate commands. Individual workspace
close/suspend/resume remains 021.

## Read before editing

021a/021b evidence; Pyzo `_savePeerWorkspacePersistence`, resource merging,
`_restorePersistedPeerEditors`, startup and application quit/restart;
root workspace persistence/session/recovery and retention coordinator tests.

## Allowed writes

Pyzo `pyzo/core/workspaceRuntime.py`, `main.py`, `applicationController.py`,
`editorGroups.py`, `menu.py`, `pyzo/_start.py`, and focused tests.
Root `spikes/peer_frames/workspace_persistence.py`, `workspace_session.py`,
`workspace_recovery.py`, `workspace_coordinator.py`, `application_lifecycle.py`,
and matching tests. This task's status/evidence at
`docs/evidence/task-021c-workspace-persistence.md` and 021 dependency status.
Document storage/retention algorithm changes require a bounded handback.

## Implementation contract

- Capture each runtime's layout/view references/state under its identity. Commit
  one shared document snapshot with the open set and active identity; preserve
  known closed and unavailable workspace records.
- Restore shared resources once, then attach each open runtime's views to that
  authority. Restore actual open views only, not tabs closed under 020. An explicitly
  empty loaded set must remain empty until an explicit New/Open action.
- A runtime restore failure is local: healthy workspaces work, the failed identity
  stays visible/retryable, and saves preserve its record. Repeated retry cannot
  duplicate views/runtimes. Keep conservative global store corruption handling.
- Store names and optional roots using existing extension/profile seams. Nested
  roots do not own documents; duplicate names must still select IDs unambiguously.
- Use existing command/menu/dialog surfaces for create/open/activate and failed
  restore retry. 021 will reuse these for reopening suspended workspaces; that
  behavior is not claimed accepted here. No separate workspace-management UI.
- Application quit/restart captures all runtimes and preserves confirmation and
  durability-before-teardown ordering. No irreversible shell termination on
  cancellation or persistence failure.

## Acceptance

- Real process restart with A/B open restores identities, layouts, unsaved
  named/untitled text and shared undo history with independent view positions.
  A previously closed tab stays closed.
- Seed known closed C: A/B restart neither loads C nor erases its metadata.
  Seed an empty open set: it remains empty; explicit New/Open works.
- Inject B restore failure: A works, B stays represented, subsequent save preserves
  B, and repair/retry restores exactly one B runtime.
- Inject quit/restart persistence failure: editors/history stay usable and shells
  are not terminated. Cancelled confirmation preserves all runtimes. Verify one
  coherent shared snapshot rather than per-workspace authoritative text copies.
- Verify single-workspace legacy migration, optional/nested roots and unchanged
  source bytes across capture/restart. Record fresh-process logs and focused
  persistence/controller/lifecycle tests before unlocking 021.

## Stop boundary

No individual workspace suspension, competing document snapshots, or full tool/
preferences integration. Any unavoidable storage migration or further service
expansion returns the smallest reproduction and bounded proposal.
