# Experiment 006: Define and exercise the peer-frame contract

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

