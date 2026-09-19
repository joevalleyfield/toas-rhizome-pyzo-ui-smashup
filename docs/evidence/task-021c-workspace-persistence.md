# 021c progress evidence: persisted workspace set

Date: 2026-09-18
Status: IN_PROGRESS

021b is complete. This task is proceeding in bounded slices:

- 021c0: capture the live coordinator/runtime set as durable workspace records. **COMPLETE**
- 021c1: restore healthy workspaces and shared resources through the runtime
  factory, isolating failed workspace records.
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
