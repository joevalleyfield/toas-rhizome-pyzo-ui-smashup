# 021c progress evidence: persisted workspace set

Date: 2026-09-18
Status: IN_PROGRESS

021b is complete. This task is proceeding in bounded slices:

- 021c0: capture the live coordinator/runtime set as durable workspace records. **COMPLETE**
- 021c1: restore healthy workspaces and shared resources through the runtime
  factory, isolating failed workspace records. **IN PROGRESS**
- 021c2: wire named create/open/activate commands and restart/quit behavior.

The existing atomic persistence store remains the single generation authority;
021c does not introduce per-workspace competing document snapshots.

## 021c0 evidence

`WorkspaceCoordinator.capture_persistence_records()` now emits the loaded
workspace IDs, active identity, and one schema-versioned record per live
runtime, including name, optional persistence location, layout, and profile
state. The capture is deep-copied so later UI mutations cannot alter the
pending generation.

Verification: `test_workspace_coordinator.py` — 17 passed.

## 021c1 progress

Pyzo save now consumes the coordinator's loaded/active workspace capture while
retaining the richer Pyzo session payload and prior profile/extension data.
Startup no longer falls back to an arbitrary remembered workspace when the
durable loaded set is empty; it also avoids creating a default editor for that
valid empty set. The runtime remains available for an explicit New/Open action.

Commits: Pyzo `9c66aa8b`, `a97066c7`, `0e509cc7`.
Verification: root persistence suite — 12 passed, 5 subtests passed; Pyzo
`main.py` compiles under the configured Python 3.12 launcher.

The fresh two-process Qt harness also completed with the required markers and
no traceback: `FIRST abc 1` and `SECOND` with clean restoration, retained
Undo/Redo, and duplicate-file identity reuse. The harness required
`QT_QPA_PLATFORM=offscreen` in this session; direct Pyzo processes were
terminated by the external, PID-scoped test cleanup after their markers.

The broader offscreen `--test` smoke reached the existing editor-dock checks
but failed an unrelated isolation assertion (`expected 2 editors, found 4`)
when run against the default persisted Pyzo configuration. It is retained as
an environment/configuration finding, not counted as 021c acceptance.

The primary live runtime is now owned by `WorkspaceRuntimeCatalog` and disposed
through that catalog, establishing the attachment point for additional loaded
workspace runtimes without changing the current single-runtime behavior.

## 021c1 runtime-set restoration

`WorkspaceRuntimeCatalog.restore_loaded()` now restores requested identities
through a record-aware factory, reuses identities already present, and returns
per-identity failures without discarding healthy runtimes. A retry therefore
cannot duplicate a successful runtime.

The persistent probe
`spikes/peer_frames/qt_workspace_set_restore_probe.py` seeds A/B, launches the
real Pyzo application twice with fresh offscreen Qt, and observes the live
application controller. Both phases passed:

```
FIRST WORKSPACES workspace-a workspace-b
SECOND WORKSPACES workspace-a workspace-b
```

Pyzo commit: `6bc7e2f9`. Runtime unit tests: 4 passed; real Qt runtime tests:
2 passed. The probe source remains in the repository for repeatable acceptance.
