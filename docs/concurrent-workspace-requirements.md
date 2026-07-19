# Concurrent workspace requirements baseline

Date: 2026-07-19

## Status and purpose

This note is the normative requirements baseline produced after the descriptive
[Experiment 013 workspace-state audit](evidence/experiment-013-workspace-state-ownership-audit.md).
It records agreed product behavior before implementation analysis, risk
ranking, migration planning, or source changes begin.

The baseline starts deliberately simple. Deferred behavior should be added only
in response to demonstrated need or explanatory UI that makes it unsurprising.

## Core model

- One Pyzo process may load several workspaces concurrently.
- A workspace is a profile-like instance of Pyzo state and preferences. It is
  not a process, window, project, recursive container, or synonym for the set
  of loaded projects.
- Workspace identity survives renaming and changes to its persistence location.
  Explicit copy or duplication creates a new workspace identity even when the
  initial state is identical.
- A project initially remains Pyzo's existing starred-directory record: path,
  display name, and existing options. Project records and options are
  workspace-local; filesystem content is shared external reality.
- Every open view belongs to one loaded workspace or to a live zombie remnant
  of a workspace. The initial model has no unscoped-view primitive.
- Selected application resources, notably document content/identity and kernel
  state, may be shared across workspace-owned views. Sharing a resource does
  not merge workspace-local state, preferences, recovery, or history.
- Copying preferences between workspaces is an explicit snapshot. Later source
  changes do not propagate automatically.

## Process restore and external ingress

- A normal application restart restores the same loaded workspace set and its
  shared document identities and relationships.
- One workspace's restore failure does not block the others. The failed
  workspace remains visibly represented as unavailable and remembered for
  retry.
- A command-line or operating-system file-open request without an explicit
  workspace targets the most recently foregrounded available loaded workspace.
- If that workspace is unavailable, ineligible, or closing, ingress uses the
  next most recently foregrounded available workspace.
- If no workspace is loaded, ingress creates a default workspace and opens the
  document there.
- Filesystem project membership does not implicitly select a workspace.

## Documents, views, and identity

- Document identity and live content may be shared by views in several
  workspaces. Editing through one view updates the shared live content seen by
  the others.
- Rename and Save As preserve document identity.
- An explicit branch creates a new document identity initialized from current
  content. Subsequent edits do not propagate between the original and branch.
- Moving a view changes its workspace assignment and carries its view-local
  state. It does not change document identity, content, dirty state, or
  recovery identity.
- Closing a non-final view needs no document disposition. Explicitly closing
  the final view globally requires Save, Discard, or Cancel.
- Unloading a workspace retains its open-view set and dirty buffers as
  workspace recovery state, including when it held the only retained view.
- Background recovery persistence never authorizes overwriting the user's
  file.

### Conflicts and recovery

- A conflict creates two content lineages under one document identity. It does
  not create a second identity implicitly.
- Resolution may merge those lineages. Preserving divergence as a separate
  identity requires an explicit branch.
- Conflict provenance is workspace-local while the conflict exists. No durable
  conflict-resolution history is required after resolution.
- An ordinary explicit Save retains its ordinary authority and metadata.
- Resolution propagates among currently loaded workspaces only when their
  conflict views have the same document identity, retained content, and
  observed external version. An unloaded workspace does not inherit the event;
  it reassesses on its next load.
- If retained content is content-identical to the current external file,
  restore reopens it as non-conflicted.
- A genuine conflict surfaces timestamps at minimum and all other available
  comparison, save, and provenance metadata.
- Each closed workspace retains its own recovery snapshot even when another
  workspace still has a live view of the shared document.
- A recovery snapshot is an immutable point-in-time version. Later edits or
  saves through another workspace do not update it.

## Workspace main and pinned views

- Each workspace may designate one main document independently of its open
  views.
- Main designation follows document identity through in-application rename or
  Save As and may survive without an open view.
- Designating a pathless document as main requires choosing and saving a path.
- Execute Main resolves the workspace from the invoking view and then uses
  that workspace's main document. The main need not have an open view.
- An unavailable main remains visibly broken until the user relocates it,
  chooses another main, or clears the designation.
- Relocating recovers the same document identity at a new location. Choosing a
  different main changes only the designation to that document's existing
  identity; neither operation merges or mutates identities.
- Pinning is defined as retaining an open view. A view that is both pinned and
  main must be unpinned before its last view may close; only the main
  designation survives without a view.

## Preferences, appearance, and affiliation

- A workspace retains its requested preference when the runtime cannot apply
  that preference independently. Capability fallback never overwrites the
  request with the effective global value.
- Effective fallback behavior is capability-specific rather than one universal
  foreground-wins rule.
- For an interpreter that supports only shared debugger selection, the
  effective mode is shared while a workspace request for independent selection
  is retained for capable interpreters.
- Per-workspace themes are aspirational and desirable, especially as a strong
  indicator of workspace affiliation. Per-workspace language is similarly
  aspirational. Until technically supported, one explicit application-wide
  effective theme and language are acceptable while workspace requests remain
  retained.
- Whenever several workspaces are loaded, every visible pane persistently and
  unobtrusively indicates its owning workspace. Extra affiliation chrome for a
  single loaded workspace is not an initial requirement.

## Tools

- Each workspace may load its own distinct view or instance of the same tool
  type.
- Tool view state is workspace-local. Tool code and installation are
  application-wide.
- Separate tool views may consume the same shared resource.
- Initially, a tool follows the foreground eligible view or resource only
  within its own workspace.
- If no eligible resource exists in that workspace, the tool is inactive or
  empty. It never falls back to activity in another workspace.
- Explicit tool-to-resource binding is deferred.

## Execution routing and assignment

- Kernels are non-exclusive application resources. Shell and debugger views
  are workspace-owned.
- Initial explicit run assignment belongs to a workspace-local document view
  and targets a durable live-shell identity.
- Assignment survives recycling the shell's kernel process. It does not
  survive application restart because live shells are not restored.
- Without explicit assignment, editor-originated execution targets the most
  recently foregrounded eligible shell in the initiating view's workspace.
- Foregrounding another eligible shell changes the implicit target for every
  unassigned document view in that workspace.
- Recency is not a fallback queue. A dead target does not silently fall through
  to an older foregrounded shell.
- Unexpected target loss leaves a visible broken assignment until the user
  reconnects that shell identity or clears the assignment back to
  workspace-implicit routing.
- Confirmed shell or workspace closure may clear affected assignments to
  implicit routing.
- Corrective choice defaults to workspace scope; explicit assignment remains
  view-local.
- Execute Selection, Line, Cell, File, and Main initially use the same target
  resolution. Their command identities remain separate so later evidence may
  justify divergence.
- Execute commands use current buffer content and do not save to disk.
- Run File/Main as Script uses the same target resolution, autosaves, and
  preserves current Pyzo behavior by recycling the resolved shell.
- Direct cross-workspace assignment, a spawn-new script policy, and UI for
  creating additional shell views on an existing kernel are deferred.

## Shell migration

- Moving a shell view to another workspace changes its view ownership but does
  not recycle its interpreter. The shell remains in a visible transitional
  state.
- A later successful kernel restart or recycle, whether explicit or caused by
  Run File/Main as Script, completes migration into the view's destination
  workspace. Failed recycling leaves the shell transitional.
- Until recycling, the live interpreter retains its existing process state.
  Newly invoked run and debug operations nevertheless use the destination
  workspace's routing, preferences, and breakpoint overlay.
- Starting a new debug session does not itself complete migration.
- An already-active debug session keeps the workspace semantics and breakpoint
  overlay with which it began until that session ends.
- Closing the destination workspace treats a transitional shell as belonging
  to that destination and closes it under normal confirmation unless the user
  first moves it elsewhere.
- Closing the source workspace does not kill an ordinary, non-debug
  transitional shell or force immediate recycling. It may retain its
  interpreter state until the user performs an operation that recycles it.
- Transitional state does not survive application restart because live shell
  state itself is not restored.

## Debugging and postmortem

- Foregrounding a shell chooses the debugger context. Next, Step, Return, Jump,
  Continue, and Stop target that shell's active debugger session directly.
- A debug action on a non-debug shell is a no-op with an optional gentle state
  reminder, never an action on a previously foregrounded session.
- Preserve current Pyzo Jump behavior and interpreter/frame restrictions. The
  debugger owns source navigation and may open or scroll appropriate views.
- Postmortem re-entry prefers durable live provenance identifying the shell or
  kernel that produced the traceback. Assignment or workspace-implicit routing
  applies only when such provenance is unavailable.
- Postmortem state is live kernel state. A dead origin has nothing resumable and
  cannot fall back to another kernel.
- Several shells may retain independent postmortem/debug sessions for the same
  document. The user interleaves them by foregrounding shells and invoking
  controls; nothing cycles automatically.
- Postmortem permits inspection and stack-frame navigation, not continued
  execution, stepping into new code, or hitting new breakpoints.

## Breakpoint overlays

- Breakpoints are persistent workspace-owned overlays on shared source
  documents. Views of one document may therefore display different breakpoint
  sets in different workspaces.
- Adding or removing a breakpoint affects only the owning workspace's overlay.
- A debug session uses the shell view workspace's overlay when that session
  begins. Its overlay does not change mid-session.
- Explicitly branching a document initially copies the branching workspace's
  breakpoint overlay to the new identity. The two overlays then evolve
  independently, and other workspaces are unaffected.
- Breakpoints for an unavailable source identity remain visible as broken,
  inactive entries and reactivate if that identity is recovered.
- The user may explicitly discard all broken breakpoint entries associated
  with one unavailable document. Per-breakpoint discard is not required
  initially.
- A path reused by another document identity does not reactivate the old
  breakpoints.

## Zombie workspaces

- Closing a workspace with an active debug or postmortem session automatically
  leaves a minimal zombie remnant. The ordinary workspace UI and durable loaded
  state close while session-critical ownership remains available.
- A zombie is not part of the normally loaded workspace set and cannot acquire
  new ordinary work silently.
- It retains the complete breakpoint overlay and enough workspace and document
  context for every dependent session.
- A zombie-backed debugger may open temporary source views owned by the zombie.
  Those views permit ordinary source editing and visibly retain zombie/workspace
  affiliation.
- Source edits follow normal document and recovery rules. Breakpoint edits made
  through zombie views are transient selections for the surviving sessions.
- The zombie persists while any dependent live debug or postmortem session
  remains and retires automatically after the last one ends. Zombie-owned views
  do not extend its lifetime.
- On retirement, zombie-owned source views close. Dirty buffers are captured in
  the closed workspace's recovery state rather than written to user files;
  clean temporary views close without recovery content.
- If the workspace is not reopened before zombie retirement, transient
  breakpoint changes are discarded and the previously saved overlay remains
  untouched.

### Reopening while a zombie exists

- Reopening the durable workspace resynchronizes its saved breakpoint overlay
  with the zombie overlay.
- Any zombie breakpoint change requires an explicit choice, even when durable
  state did not change, because reopening may intentionally mean reverting to
  saved state.
- The available choices are Use Saved, Use Zombie, and Merge.
- A live debugging session blocks full workspace reopening until reconciliation
  completes.
- Postmortem-only inspection does not block full reopening because it cannot
  hit new breakpoints. However, the workspace cannot start a new debug session
  while breakpoint reconciliation remains deferred.
- The selected reconciliation result becomes the workspace's durable overlay
  without invalidating already captured postmortem inspection state.

## Deliberately deferred behavior

- Explicit tool-to-resource binding.
- Richer execution-affinity chrome and cross-workspace targeting.
- Multiple shell views over one kernel.
- Alternative Run-as-Script recycle-versus-spawn policy.
- Fully independent per-workspace theme and language when platform capability
  is unknown.
- A general unscoped or transient-open document/view primitive.
- Implementation priority, migration order, serialization format, and source
  ownership changes. Those require a separate follow-up analysis grounded in
  this baseline and the Experiment 013 audit.

## Resolved status

No product-semantics question in this baseline blocks handoff to follow-up
analysis. Deferred capabilities are explicit non-requirements for the initial
behavior rather than unresolved assumptions.
