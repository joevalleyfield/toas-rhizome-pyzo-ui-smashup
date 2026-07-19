# Experiment 013: Audit workspace state ownership

## Status

Ready. This artifact grounds the audit requirements accepted on 2026-07-18.
The audit has not commenced, and no Pyzo source or test changes are authorized
by this task.

## Objective

Inventory every persisted and live Pyzo state/configuration entry point and
describe its actual ownership, storage, consumers, persistence, and lifecycle.
Compare those current contracts with the provisional concurrent-workspace
semantics below, without implementing migrations or ranking the findings.

The audit should crystallize contracts that are currently loose because stock
Pyzo assumes one application-wide workspace. It is descriptive first, but may
record evidence-backed candidate future scopes as explicitly provisional
forward direction.

## Grounding workspace model

- One Pyzo process may load multiple workspaces concurrently.
- A workspace is a profile-like Pyzo state and preference instance, not a
  process, window, project, or recursively composable container.
- Every pane/view belongs to exactly one workspace.
- A workspace independently owns its commands, persistence, lifecycle, layout,
  open-view set, main-file designation, contextual preferences, and project
  records.
- Selected application resources, including document and kernel identity, may
  be represented through views in more than one loaded workspace.
- Sharing a resource does not merge workspace-local preferences or history.
- Workspace preference transfer is an explicit snapshot copy. Later source
  changes do not propagate automatically.

These are initial normative candidate requirements for gap analysis. The audit
may expose contradictions or excessive complexity that require revising them;
it must not silently rewrite them.

## Candidate resource and lifecycle semantics

### Projects and preferences

- Initially, a project is exactly Pyzo's existing starred-directory record:
  path, display name, and existing options.
- Project records and options are workspace-local. The same physical directory
  may have different names and options in different workspaces.
- Filesystem content remains shared external reality.
- Copying project or workspace preferences creates an independent destination
  snapshot.
- Initial semantics need explicit add, remove, and snapshot-copy operations,
  not a distinct `Move Project` abstraction. Richer project identity and move
  semantics remain deferred until actual usage supplies a stable handle.

### Documents and views

- Views are workspace-owned; document identity and content may be shared by
  views in several workspaces.
- Shared document views see the same live content. Intentional divergence is an
  explicit branch that creates a new identity initialized from current content;
  edits never propagate automatically between original and branch.
- Moving a view changes its workspace assignment and carries all view-local
  state without changing document identity, content, dirty state, or recovery
  identity.
- Dirty buffers are persisted automatically to recovery storage only. Background
  persistence never authorizes overwriting a user's file.
- Closing a non-final view needs no document disposition. Explicitly closing
  the final view globally requires Save, Discard, or Cancel.
- Unloading a workspace retains its open views and dirty buffers as workspace
  state, including when it contains the only retained view. Reload may therefore
  require conflict resolution.
- A restored conflict preserves retained identity/content and never merges or
  overwrites automatically. Surface retained/external timestamps at minimum and
  all other available comparison/provenance metadata.
- Ordinary explicit Save keeps its normal authority while conflicted. Conflict
  history is workspace-local. Resolution propagates only among currently loaded
  workspaces holding an identical conflict: same document identity, retained
  content, and observed external version. Unloaded workspaces reassess later.

### Main files

- Each workspace may designate one main file independently of its open panes.
- The designation follows document identity through in-application rename or
  Save As.
- Designating a pathless document as main requires choosing and saving a path.
- Execute Main resolves the workspace from the invoking pane, then uses that
  workspace's main file. The file need not have an open pane.
- A current document view contributes its explicit run assignment; invocation
  from a non-document pane uses workspace implicit routing.

### Execution assignment

- Without explicit assignment, editor-originated execution targets the most
  recently foregrounded eligible shell in the same workspace.
- Foregrounding another eligible shell immediately changes this implicit target
  for every unassigned document view in that workspace.
- Recency is not a fallback queue. If the implicit target dies, an older shell
  is not selected merely because it was previously foregrounded. A newly
  foregrounded shell or corrective user choice establishes the new workspace
  implicit target; corrective choice defaults to workspace scope.
- Explicit assignment belongs to a workspace-local document view, targets
  durable shell identity, and overrides foreground routing.
- Assignment is live-session state only. It is not persisted through workspace
  save/open or application restart because shell state is not restored.
- View migration carries explicit assignment even if that temporarily produces
  cross-workspace targeting. Direct cross-workspace assignment and additional
  shell views on an existing kernel are deferred until explanatory chrome
  exists.
- Assignment survives recycling the shell's kernel process. Confirmed shell or
  workspace closure may clear affected assignments to implicit routing;
  unexpected target loss leaves a visibly broken assignment until reconnect or
  explicit correction.
- Small Execute commands (selection, line, cell, and advance variants) and
  Execute File/Main share one initial assignment. Retain their separate state-
  matrix rows so evidence can justify divergence later.
- Execute commands use current buffer content and do not save to disk.
- Run File/Main as Script uses the same target resolution, autosaves, and
  preserves current Pyzo behavior by recycling the resolved shell. No new
  cross-workspace confirmation or spawn-new policy is required initially.

### Kernels and debugging

- Kernels are non-exclusive application resources; each shell/debugger view is
  workspace-owned. UI for creating additional shell views on an existing kernel
  is deferred.
- Shared debugger selection is the portable default. Independent per-view or
  per-workspace selection is available only when an interpreter explicitly
  advertises that capability, with unobtrusive mode indication.
- Foregrounding a shell selects its debugger context. Next, Step, Return, Jump,
  Continue, and Stop target that shell's active debugger session directly.
- A debug action on a non-debug shell is a no-op with an optional gentle state
  reminder, not an action on a previously foregrounded session.
- Preserve current Pyzo Jump behavior and interpreter/frame restrictions; the
  debugger session owns source navigation and may open or scroll appropriate
  editors.
- Post-mortem re-entry prefers durable live provenance identifying the kernel
  that produced the traceback. Assignment or workspace implicit routing applies
  only when no such provenance exists.
- Post-mortem state is live kernel state. A dead origin has nothing resumable
  and cannot fall back to another kernel.
- Several shells may retain independent post-mortem/debug sessions for the same
  document. Nothing cycles automatically: the user interleaves sessions by
  foregrounding shells and invoking controls.

## Audit scope

The inventory includes, at minimum:

- the complete `pyzo.config`/defaults tree and all config mutations;
- application, workspace/session, frame, group, pane, and view state;
- editor/document identity, main-file state, recent files, dirty recovery, and
  conflict metadata;
- shell/kernel configuration, current/foreground shell, run assignments,
  execution history, debugger and post-mortem state;
- tool/plugin configuration, tool instance state, and file-browser starred
  projects/current paths;
- menus, commands, shortcuts, status, appearance, language, and other global
  settings;
- startup, restore/migration, restart, shutdown-only, and compatibility-facade
  state;
- derived or cached runtime state even when it has no persisted representation.

The audit must search dynamically created tool/plugin settings and deprecated
or read-only fields rather than limiting itself to known interesting settings.

## Required matrix schema

Every row must record:

1. stable state identity;
2. storage/source location;
3. producers/writers;
4. consumers/readers;
5. persistence and lifetime;
6. current effective scope;
7. mixed-scope notes;
8. candidate future scope, clearly marked provisional;
9. supporting source/runtime evidence; and
10. unresolved questions.

Candidate scopes include application, workspace, pane/view, shared resource,
and explicit mixed contracts. Current storage scope and effective semantic scope
must be recorded separately.

## Evidence rules

- Source inspection is the default evidence source.
- Use existing accepted runtime evidence where it directly proves a row.
- Run focused, non-destructive probes whenever consequential scope or lifecycle
  behavior cannot be established confidently from source and existing evidence.
- A probe may be omitted for an ambiguity with no meaningful downstream effect,
  but the row must record that rationale.
- Clearly distinguish observed behavior, source inference, candidate future
  direction, and unresolved uncertainty.
- Produce a source census of configuration/state entry points and explain how
  it establishes coverage.

## Acceptance criteria

- Every discovered Pyzo persisted or live state/configuration entry point has a
  matrix row.
- Every row contains all required schema fields or an explicit not-applicable
  rationale.
- Mixed contracts name every observed participating scope rather than being
  forced into one owner.
- Every consequential ambiguity has runtime evidence or remains an explicit
  unresolved finding.
- Every omitted runtime probe has a recorded no-meaningful-effect rationale.
- The source census covers config helpers, dynamic tool/plugin state, services,
  widgets, recovery/session stores, startup/restore, and shutdown writers.
- Current behavior and candidate future requirements are never conflated.
- The audit records no severity, priority, implementation order, source fix, or
  migration patch.
- The full matrix and evidence are written to
  `docs/evidence/experiment-013-workspace-state-ownership-audit.md`.

## Allowed write surface

- This task artifact.
- `docs/evidence/experiment-013-workspace-state-ownership-audit.md`.
- `EXECUTION_CHECKLIST.md` and the ignored local `.codex/HANDOFF.md` for audit
  progress only.
- Temporary files outside the repository for non-destructive probes.

No Pyzo, QtADS, binding, spike source, test, configuration, or user-data writes
are allowed. If a probe demonstrates that instrumentation is genuinely required,
record that as a blocker or follow-up rather than editing source during this
audit.

## Follow-up boundary

After the descriptive audit is accepted, a separate analysis may assess
multi-workspace consequences, assign severity/priority, revise candidate
semantics, and route bounded implementation work. That analysis is not part of
Experiment 013's initial audit.
