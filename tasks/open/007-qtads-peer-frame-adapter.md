# Experiment 007: Back peer frames with QtADS

## Status

Claimed for implementation on 2026-07-14.

## Objective

Implement the Experiment 006 contract over QtADS and determine whether its
privileged manager/root can remain a completely private implementation detail.

## Dependencies

- Experiment 006 is complete and its contract tests are reusable against a
  real backend.

## Acceptance criteria

- Two or more visible frames are behaviorally interchangeable regardless of
  creation order or their QtADS container type.
- Any test pane type can be the first pane in any frame.
- The adapter passes contract scenarios for tabs, nested local splits, outer
  splits, floating, cross-frame movement, and re-docking.
- Drag targeting works within the source frame and across overlapping frames,
  selecting the foremost eligible frame under the pointer.
- Closing an empty or populated frame does not implicitly quit the application
  or bypass pane close negotiation.
- Layout save and restore preserve peer frames without exposing a main-frame
  identity in the application format.
- The experiment explicitly tests first-pane, last-pane, source-frame, root-
  frame, and floating-frame cases rather than validating only symmetric-looking
  layouts.
- Every unmet invariant is localized to adapter policy, unavailable binding
  API, or QtADS source behavior with a minimal reproduction.

## Allowed write surface

- A root-level standalone adapter spike and tests.
- QtADS instrumentation or a temporary patch surface needed to establish a
  minimal reproduction.
- Experiment notes and this task artifact.
- No Pyzo product integration in this task.

## Completion evidence

Record the scenario matrix, automated and interactive procedures, traces for
failed invariants, whether the privileged root is observable to users, and the
smallest candidate source changes. Do not adopt candidate fork changes as
permanent architecture in this task.

## Progress evidence

### Private-root projection

`spikes/peer_frames/qtads_backend.py` implements the first stock-QtADS backend
slice. A parentless `CDockManager` is retained as a hidden, empty coordinator;
every application-visible frame is created as a `CFloatingDockContainer`.
Consequently the first-created frame and later frames have the same QtADS type
and none is the manager/root container.

The offscreen adapter suite currently proves:

- editor, shell, tool, and run/debug pane kinds can each create a frame;
- tabs, local splits, outer splits, floating, and cross-frame movement project
  into peer floating containers;
- closing the first-created frame does not request application shutdown;
- application-format layout restoration recreates the peer topology while the
  manager remains hidden and empty.

No Pyzo, binding, or QtADS source change was required for this slice.

The remaining boundary is reverse synchronization. Direct user drags currently
change QtADS state without updating the authoritative application model. The
next slice must capture completed QtADS layout mutations, preserve stable frame
and group identities where objects survive, assign identities to newly created
frames/groups, and submit the resulting topology through the application
contract. Overlapping-frame drag targeting and lifecycle interception remain
interactive acceptance work after that loop is closed.
