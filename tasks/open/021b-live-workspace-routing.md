# 021b: Attach and route two live workspace runtimes

## Status

WAITING — intended executor Luna. Dependency: 021a complete and committed.
Follow the [prerequisite review](../021-runtime-prerequisites.md) and
[batch contract](../local-retention-batch.md).

## Outcome

Two workspaces in one process display real peer editors and share editing state,
with operations routed by their originating workspace. Keep the second-runtime
entry point restricted to isolated tests/development until 021c makes restart safe.

## Read before editing

021a evidence/API; Pyzo controller, editor group/tab creation and file deduplication,
shell host ownership, menu dispatch, focus and close callbacks; root coordinator
ownership epochs, document registries and lifecycle policies.

## Allowed writes

Pyzo `pyzo/core/workspaceRuntime.py`, `main.py`, `applicationController.py`,
`editorGroups.py`, `editorTabs.py`, `shellGroups.py`, `menu.py`, and focused tests.
Root `spikes/peer_frames/workspace_coordinator.py`, `qtads_backend.py`,
`qtads_commands.py`, `qtads_status.py`, `application_lifecycle.py`, `lifecycle.py`,
`document_resources.py`, and matching tests, for ownership
and routing only. This task's status/evidence at
`docs/evidence/task-021b-live-workspaces.md` and 021c dependency status.

## Implementation contract

- Construct A and B through 021a's factory with distinct backends/frames and
  unambiguous pane identities. Add workspace-addressed new/open/reopen and lookup.
- Opening A's document in B creates a B view of the same resource, not merely
  focus A's editor. Bind both to the existing shared document adapter; selection,
  scroll, pinning and placement remain view-owned.
- Activation updates coordinator context. Close, Save, Discard, dialogs, metadata
  and retained reopen resolve the actual owner after focus changes. Failed/stale
  destinations leave neither a registered phantom view nor an orphan widget.
- Show workspace affiliation on visible panes/frames when both are loaded.
  Preserve shell/tool ownership; refuse native cross-workspace shell drops before
  movement. Safely route exposed commands or mark unsupported routes unavailable.
  Full execution integration and successful buffer transfer remain later work.
- Application frame counts/cleanup cover all runtimes. Closing A's final frame
  cannot quit or tear down B. Workspace suspension remains 021.

## Acceptance

- Render A/B simultaneously in real Qt. Edit, undo and redo the same named
  document from both; assert shared identity/text/dirty state/history, independent
  selection/scroll. Repeat shared-view coverage with an untitled document by ID.
- With B foreground, close A's view: B stays live, history intact, no final-document
  retention. Close the globally final view: retain once; reopen explicitly into B.
  Failed reopen leaves no phantom view. Preserve retention-failure cancellation.
- A callback captured in A still addresses A after focus in B; removed ownership
  is rejected. Verify shared Save/Discard effects and source writes only on Save.
- Cross-workspace shell drop refusal leaves both models and Qt layouts unchanged;
  within-workspace shell behavior and 021a regressions still pass.
- Record isolated two-runtime smoke evidence and focused regression results.
  Do not claim durable multi-workspace availability before 021c.

## Stop boundary

No model-only substitute, focus-driven global rebinding, execution framework, or
duplicated retention authority. If a legacy command cannot be safely routed or
disabled within these files, return its reproduction and smallest missing seam.
