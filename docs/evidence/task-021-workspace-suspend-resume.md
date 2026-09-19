# 021 progress evidence: workspace suspend and resume

Date: 2026-09-19
Status: IN_PROGRESS

021c is complete and this task is now active. The first live slice adds
explicit `application.workspaces.close(identity)` and
`application.workspaces.reopen(identity)` operations over the existing runtime
catalog and coordinator.

## Close/reopen slice

Workspace close now performs the existing document/shell confirmation
transaction, drains all remaining workspace-owned panes, removes the runtime
from the loaded coordinator set, preserves the closed workspace record and
shared resources in the durable generation, and disposes only that runtime.
Owner-scoped editor, shell, and dock teardown no longer assumes the primary
runtime.

Explicit reopen reconstructs the runtime through 021c's factory, restores its
persisted views/layout, activates it, and commits the new loaded set.

The persistent configured Qt probe
`spikes/peer_frames/qt_workspace_set_restore_probe.py` passed:

```
CLOSE WORKSPACES workspace-b
REOPEN WORKSPACES workspace-a workspace-b
```

The close phase verified A's record remained while the persisted loaded set
became B-only. A fresh process started with B only, then reopened A explicitly.
The probe uses deterministic test-owned dirty-document and shell decisions;
production confirmation paths remain unchanged.

Pyzo changes are currently uncommitted in this slice. Focused verification:
Pyzo controller/runtime tests — 5 passed; root workspace/lifecycle/document
tests — 89 passed, 12 subtests passed.

## Remaining 021 acceptance

The shared-document close/edit/undo/restart/reopen matrix, close-both and
reopen-one flow, untitled/optional-root cases, failed restore, cancelled close,
live/debugging shell confirmation, persistence-failure rollback, and rejected
cross-workspace shell movement still require evidence.
