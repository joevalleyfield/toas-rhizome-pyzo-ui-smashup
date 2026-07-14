# Peer-frame contract spike

This spike makes the application topology executable without choosing a GUI
toolkit. The `WorkspaceModel` owns pane identity, peer-frame layout, active
context, persistence, and close transactions. A backend receives complete
serializable snapshots and reports user gestures as `BackendEvent` values.

The contract has three deliberate boundaries:

- Pane descriptors carry identity and type, but document, interpreter, and
  debugger state stays in application services outside this model.
- Frames have identical data and operations. Creation order has no semantic
  meaning and the serialized format has no distinguished frame.
- Backend destruction is never interpreted as permission to close. Pane,
  frame, and application close requests pass through application policies.

## State transitions

| Request | Required precondition | Applied result |
| --- | --- | --- |
| Create frame | Registered, unplaced pane | New peer frame with one group |
| Tab | Placed source and target | Source joins target group |
| Split | Placed source and target | Source receives a new adjacent group |
| Outer split | Placed source and target | Target frame root receives a new edge group |
| Float | Placed pane | Pane becomes the first group in a new peer frame |
| Activate | Placed pane | Pane and containing group become active context |
| Close pane | All close votes permit | Pane identity is retired |
| Close frame | Every contained pane permits | All pane closes commit together |
| Shut down | Every pane permits | Panes close, then application shutdown is requested |
| Restore | Valid registered identities and supported schema | Layout replaces current topology atomically |

Unsupported capabilities, invalid identities, refusals, and cancelled
confirmations leave the topology unchanged. An unexpected backend destruction
causes the authoritative snapshot to be re-published.

## Serialized shape

```json
{
  "schema": 1,
  "active_pane_id": "editor-1",
  "frames": [
    {
      "id": "workspace-a",
      "root": {"type": "group", "group_id": "group-1"},
      "groups": [
        {
          "id": "group-1",
          "panes": ["editor-1", "shell-1"],
          "active_pane_id": "editor-1"
        }
      ]
    }
  ]
}
```

Pane state is intentionally absent. A later application service resolves each
stable pane identity to its document, interpreter, debugger, or tool state.

Run the deterministic contract suite from the repository root:

```sh
python3 -m unittest spikes.peer_frames.test_contract -v
```

The next adapter experiment should implement the backend protocol and replay
this suite's state transitions against a real docking system. Backend-specific
objects remain below that adapter.

## Stock QtADS adapter slice

`QtAdsPeerFrameBackend` tests a private-root deployment without changing QtADS:

- A parentless `CDockManager` remains hidden and contains no dock areas.
- Every application frame is represented by the same
  `CFloatingDockContainer` type.
- The application snapshot is projected into tabs, local splits, outer splits,
  floating frames, cross-frame moves, and frame closure.
- The application serialization format restores the same peer topology without
  encoding the hidden manager.

Run its offscreen suite with the published binding:

```sh
UV_CACHE_DIR=/tmp/pyzo-uv-cache \
PYTHONPYCACHEPREFIX=/tmp/peer-frame-pyc \
QT_QPA_PLATFORM=offscreen \
uv run --offline --python 3.12 --with PySide6-QtAds \
  python -m unittest spikes.peer_frames.test_qtads_backend -v
```

This first adapter is intentionally one-way: application snapshots drive
QtADS. Translating completed user drag operations back into the authoritative
model is the next seam to prove. Until that exists, QtADS can temporarily hold
a layout that differs from the application snapshot after direct interaction.
