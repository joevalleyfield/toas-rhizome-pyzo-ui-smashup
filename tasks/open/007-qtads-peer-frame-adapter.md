# Experiment 007: Back peer frames with QtADS

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

