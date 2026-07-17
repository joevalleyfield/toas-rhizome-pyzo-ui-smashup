# Application Topology

## Guiding requirement

The application owns the workspace topology. Windows are interchangeable
views into that topology; no user-visible window is privileged as the main
workspace window.

This is a user-space requirement, not a commitment to Pyzo, Qt Advanced
Docking System (QtADS), or any other deployment technology. Those projects
may supply capabilities, prototypes, or reusable implementation machinery,
but their internal ownership models do not define the product.

## Logical model

```text
App
  |-- document and buffer state
  |-- shell and kernel state
  |-- run and debugger services
  |-- commands and application chrome
  `-- workspace layout manager
       |-- peer frame
       |    `-- pane views
       |-- peer frame
       |    `-- pane views
       `-- docking backend
            `-- QtADS prototype, fork, or replacement
```

The workspace layout manager is an application service. A docking backend may
have implementation-specific controllers, widgets, roots, or hidden objects,
but those are private backend details. They must not create a distinguished
window in the user model.

## Workspaces, projects, and resource affinity

The application may host multiple workspaces at once, and one workspace may
contain multiple projects. A frame belongs to exactly one workspace; panes from
different workspaces cannot be mixed in one frame. That frame rule does not
make a workspace the permanent owner of every resource displayed there.

- A shell owns its kernel, current working directory, environment, and history.
  Moving its pane to another workspace does not silently alter them.
- A file-browser pane owns its navigation root and state. Multiple independent
  file browsers may coexist in one frame.
- A document retains its identity when its editor pane moves. Project identity
  may be inferred from its path or explicitly pinned.
- A resource may remember the workspace or project that supplied its creation
  defaults without being permanently trapped there.

Moving a pane across workspace frames is therefore an application transfer
operation with a contextual-affinity update, not merely an unobserved docking
gesture. Resource identity and spawn provenance remain stable unless an
explicit operation changes them.

## Peer frames and panes

Every visible workspace frame is a peer. The user should not need to know
which frame was created first or which backend object coordinates the layout.

- Any editor, shell, or tool pane can be the first pane in a frame.
- Any pane can move, split, group, float, or re-dock wherever its own
  lifecycle policy permits.
- Closing, moving, or merging a frame does not invalidate application-global
  state.
- Closing one particular frame does not inherently mean quitting the
  application.
- Layout persistence describes peer frames and pane placement without
  exposing a privileged main-frame concept.
- Menus, commands, status, focus, and other application chrome follow the
  active context without making that frame the owner of the application.

The editor, shell, file browser, run/debug surfaces, and future toas transcript
views are pane types within this model. A pane type does not receive special
placement rights merely because it bootstrapped the application.

## Documents and editor views

Document state is not owned by a workspace frame or docking container. At
minimum, each open editor is responsible for the persistence and dirty state
of its document. If multiple editor views over one buffer are supported, that
state belongs to the shared document or buffer instead.

- Moving or re-docking an editor never changes its dirty state.
- Closing one of several views over the same document does not close the
  document.
- Closing the final view of a dirty document invokes save, discard, or cancel
  policy.
- Closing a frame containing several documents must respect every affected
  document's close decision and must not silently discard work.
- Application Quit and Restart automatically retain dirty named and untitled
  documents in durable recovery snapshots. This application-only disposition
  does not appear during ordinary pane or frame closure.
- A recovered snapshot remains authoritative until explicit Save or Discard.
  External disk changes produce a conflicted dirty buffer without overwriting
  the disk file.
- Debugger source navigation targets document/editor services rather than a
  particular frame.

Multiple views over one buffer are an architectural allowance, not a
first-prototype requirement.

## Shell and kernel lifecycle

Shell state is likewise independent of frame placement. Moving, grouping, or
closing a frame must not accidentally terminate a running interpreter.

- A dead shell may close without a running-process warning.
- A running shell may veto closure or require explicit confirmation that the
  interpreter will be terminated.
- Pane and frame close operations must use shell lifecycle policy rather than
  merely hiding a widget.
- Detachable and reconnectable kernels, similar in spirit to Jupyter, are a
  possible future capability but are not required by the current prototype.

Until kernel detachment exists, conservative refusal or confirmation is
preferable to implicit termination.

## Run and debugger invariants

Run, live-debug, and post-mortem state belong to application services, not to
the frame displaying a shell or editor. Layout changes must preserve:

- the active interpreter and selected debugger frame;
- traceback and source navigation;
- breakpoints and debug indicators;
- live execution against a selected captured stack frame;
- re-entry into an existing post-mortem session.

A pane may display or control this state, but moving or closing a display must
not silently destroy the underlying debugging session.

Focus and execution affinity are separate. Focus selects the pane targeted by
ordinary commands; it must not silently bind an editor to the last-focused
kernel. Direct input in a shell is unambiguous, but editor-originated Run and
Debug commands resolve an execution target in this order:

1. a target selected for the invocation;
2. a target pinned to the document, view, project, or launch configuration;
3. the only eligible target in the relevant frame or workspace;
4. an explicit chooser when more than one target remains eligible.

Remembered affinity must remain visibly inspectable near Run/Debug controls.
Textual identity is required; color may reinforce but cannot be the sole
indicator. Docking focus transitions, pane movement, and workspace transfer
must not rewrite this affinity.

## Closing and application lifetime

Frame closure is a coordinated lifecycle operation over the panes it contains.
Each affected document, shell, and tool receives an opportunity to close,
persist, terminate, hide, or veto according to its own policy. Application
shutdown is a separate decision made by the application after considering the
remaining workspace and background state.

The exact policy for an empty workspace remains open. Plausible choices
include retaining an empty peer frame, keeping the application alive without
frames on platforms that support it, or initiating application shutdown. None
of those choices requires a main window.

## Docking technology boundary

QtADS is currently useful evidence for Visual Studio-like splitting, grouping,
floating, overlays, and layout persistence. It is not presumed to be the final
workspace architecture.

The current QtADS prototype exposes mismatches with this model:

- its manager is also a widget and root dock container;
- the manager/root and floating containers have different behavior;
- root-window close and z-order semantics leak implementation privilege;
- dock closability can determine whether an entire floating container closes;
- simple widget hiding does not implement Pyzo document or shell lifecycle.

These findings are constraints to evaluate, not product requirements to adopt.
The docking backend may be wrapped, selectively modified, forked, or replaced.
A successful backend preserves the peer-frame model and pane lifecycle even if
its private implementation contains asymmetric objects.

## Open questions

- How should application chrome be projected into peer frames on macOS,
  Windows, and Linux?
- Can QtADS reliably present only peer frames while keeping its privileged
  root entirely private, or does that require a fork?
- What is the transactional behavior when closing a frame containing several
  dirty documents and running shells?
- How should peer-frame geometry and active context be serialized?
- When should an empty workspace keep the application alive?
- Which resource types may transfer between workspaces, and which require an
  explicit clone, reconnect, or refusal operation?
