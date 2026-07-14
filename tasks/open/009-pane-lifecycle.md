# Experiment 009: Separate pane, frame, and application lifecycle

## Objective

Prove that document and interpreter lifecycle remains correct when panes and
peer frames are closed, moved, or restored through the docking backend.

## Dependencies

- Experiment 006 defines close negotiation and state transitions.
- Experiment 007 provides the backend behavior under frame closure.
- Experiment 008 may supply real Pyzo panes; a model pane may be used first.

## Acceptance criteria

- Closing a non-final editor view leaves its document alive.
- Closing the final dirty editor view supports save, discard, and cancel.
- Closing a frame containing multiple dirty documents is transactional: a veto
  or cancellation does not leave an accidental partial close.
- A dead shell can close directly.
- A running shell refuses closure or requires explicit confirmation; moving or
  regrouping it never implies interpreter termination.
- Closing the first-created frame behaves like closing any other frame and does
  not inherently quit the application.
- Empty-frame behavior and application-shutdown policy are explicit and tested
  separately.
- Backend widget hiding or destruction cannot bypass application lifecycle
  policy.

## Allowed write surface

- Peer-frame contract and lifecycle implementation/tests.
- The local Pyzo project surface needed for document and shell policy.
- Root-level experiment notes and this task artifact.

## Completion evidence

Record a state matrix covering clean/dirty documents, final/non-final views,
dead/running shells, single/multiple panes, and frame/application closure.
Include automated results and any backend event paths that required interception.

