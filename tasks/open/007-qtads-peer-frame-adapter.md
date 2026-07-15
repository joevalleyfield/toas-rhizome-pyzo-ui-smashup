# Experiment 007: Back peer frames with QtADS

## Status

Complete on 2026-07-15. Retained in `open/` because the repository queue does
not yet define task-movement protocol.

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

### Reverse synchronization

The adapter now captures QtADS topology after coalesced floating-container area
signals and submits it through an atomic, placement-only
`WorkspaceModel.adopt_backend_layout()` operation. It preserves identities on
surviving frame windows and dock areas, assigns identities to new floats and
groups, normalizes unary QtADS splitter wrappers, and carries active-tab context
from the emitting area.

Application-driven rendering suppresses reverse adoption. During user drags,
capture waits until no floating window reports an active drag. Missing,
duplicate, or unknown panes and manager/root contamination are rejected; the
authoritative layout is then restored. Live floating windows are rediscovered
from the QtADS registry before rendering, so deleted Qt wrappers are never
dereferenced.

The combined deterministic suite now has 25 passing tests. Direct QtADS
mutations cover cross-frame tabs, local and outer splits, new floating frames,
active-tab changes, coalescing a source/target signal burst into one adoption,
physical pane-removal rejection, manager/root-contamination rejection, and
post-adoption idempotence. A deterministic multi-area frame merge also proves
that the target frame identity survives, the emptied source frame disappears,
and surviving source group identities are retained in one adoption.

`spikes/peer_frames/qtads_demo.py` is the interactive acceptance surface. It
begins with overlapping peer frames and prints the application topology after
each settled drag. The following native mouse pass completed that validation.

### Native mouse acceptance

The interactive demo was exercised on macOS against overlapping native
windows. The user reported that the behavior was well-behaved and completed
the requested local move, overlapping-window drop, floating, tabbing, split,
and whole-frame merge cases. The order differed from the suggested script but
does not affect the captured invariants.

The trace recorded nine successful settled adoptions:

- a run/debug pane tabbed into the file-browser frame;
- tab activation changes in that group;
- the file-browser pane floated into new `frame-user-1` / `group-user-1`
  identities and then re-docked;
- the file-browser and run/debug panes split horizontally into a new group and
  then tabbed together again;
- the shell frame merged into the file-browser frame while preserving
  `group-3` and removing the emptied `workspace-shell` frame;
- the two-tab editor frame merged into the same surviving frame while
  preserving `group-1` and removing `workspace-editor-one`.

The final application topology contained one peer frame with three horizontal
groups: shell, file-browser/run-debug tabs, and the two editor tabs. Every one
of the five original pane identities appeared exactly once, active-pane state
remained valid, the target frame identity survived, and no manager/root frame
appeared.

### Experiment conclusion

Stock QtADS can back the technology-neutral peer-frame topology without
exposing its privileged root for the scenarios in this experiment. The root
still exists privately as an empty coordinator, but all visible frames are
peer `CFloatingDockContainer` instances. No QtADS or binding fork is currently
required for peer-frame creation, layout projection, reverse synchronization,
overlapping-window docking, or application-format restoration.

Pane-specific close behavior remains intentionally outside this conclusion and
belongs to Experiment 009. Pyzo surface ownership and command projection belong
to Experiment 008.
