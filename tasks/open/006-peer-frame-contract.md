# Experiment 006: Define and exercise the peer-frame contract

## Status

Complete on 2026-07-14. Retained in `open/` because the repository queue does
not yet define task-movement protocol.

## Objective

Create the smallest technology-neutral API and deterministic harness that can
state the application's peer-frame and pane-lifecycle requirements without
mentioning Pyzo, QtADS, `QMainWindow`, dock widgets, or floating containers.

## Dependencies

- The topology in `docs/application-topology.md` is the governing requirement.
- Evidence from Experiment 003 may inform operations but must not leak backend
  types into the contract.

## Acceptance criteria

- The contract represents stable pane identity, peer-frame identity, pane type,
  placement, grouping, splits, active context, and serializable layout.
- It supports creating a frame from any pane type and moving a pane within or
  between frames without changing pane ownership.
- It distinguishes a request to close a pane, close a frame, and shut down the
  application.
- Close negotiation can allow, refuse, confirm, or cancel without partially
  closing a multi-pane frame.
- Backend-originated focus, move, split, group, float, close, and destruction
  events have defined application-level results.
- A deterministic fake or model backend exercises every operation and checks
  that no frame has privileged semantics.
- The contract defines capabilities and failure results for operations a
  backend cannot provide.

## Allowed write surface

- A new root-level contract or spike surface outside `deps/`.
- Contract-focused tests and fixtures.
- Documentation immediately describing the contract.
- This task artifact for evidence.

## Completion evidence

Record the public contract, state-transition table, executable verification
command, representative serialized layout, and unresolved policy choices.

## Result

`spikes/peer_frames` implements a pure-Python `WorkspaceModel` and deterministic
`FakeBackend`. The application model owns pane registration, peer-frame layout,
active context, serialization, capability results, and close negotiation. The
backend receives complete snapshots and reports gestures as application-level
events; an unexpected destruction is rejected and causes authoritative state
to be re-published.

The contract suite covers:

- every pane kind as the first pane of a frame;
- tabbing, local splits, outer splits, floating, and cross-frame movement;
- stable pane identity and removal of empty source frames;
- backend gesture translation and destruction rejection;
- transactional allow, refuse, confirm, and cancel close outcomes;
- separation of frame close from application shutdown;
- layout round trip with no privileged frame identity;
- capability failure and malformed restore without state mutation.

Verification from the repository root:

```sh
UV_CACHE_DIR=/tmp/pyzo-uv-cache \
PYTHONPYCACHEPREFIX=/tmp/peer-frame-pyc \
uv run --offline --python 3.12 \
  python -m unittest spikes.peer_frames.test_contract -v
```

Result: 10 tests passed. `git diff --check` also passed.

The public contract, transition table, and representative serialized layout are
documented in `spikes/peer_frames/README.md`.

### Open policy choices

- This first model removes a frame when its last pane leaves. Whether a product
  retains empty frames remains an application policy to resolve.
- Close confirmation is generic in this contract. Document save/discard and
  running-interpreter choices belong to Experiment 009.
- Split weights and frame geometry are intentionally deferred until the real
  adapter demonstrates the backend-independent representation they require.
