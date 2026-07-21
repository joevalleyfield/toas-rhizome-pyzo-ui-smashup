# Experiment 014: Implement concurrent workspaces

## Status

Stage 1 accepted on 2026-07-20. Stage 2 is next. No persisted multi-workspace
format or user-data migration has begun.

This task stages implementation of the accepted
[concurrent-workspace requirements](../../docs/concurrent-workspace-requirements.md)
through the proof obligations identified by the
[risk analysis](../../docs/concurrent-workspace-risk-analysis.md). Each stage is
an independent acceptance and commit boundary. Do not begin a later stage until
all acceptance evidence for its dependencies is recorded here.

## Objective

Replace Pyzo's one-application-workspace assumptions with explicit concurrent
workspace identity and ownership while preserving shared document/kernel
resources, recovery safety, peer-frame behavior, vanilla Pyzo fallback, and the
accepted Run/Debug/postmortem workflows.

The first implementation must realize the complete initial behavior in the
requirements baseline. Deferred capabilities remain out of scope unless a
stage exposes a blocker that cannot be resolved within the accepted simpler
contract.

## Dependencies

- Experiment 012: peer startup has no `QMainWindow`, while legacy Pyzo remains
  supported.
- Experiment 013: current persisted and live state ownership is fully audited.
- `docs/concurrent-workspace-requirements.md`: normative product behavior.
- `docs/concurrent-workspace-risk-analysis.md`: technical risk register and
  proof obligations.
- Existing document/shell lifecycle, recovery, workspace-session, command,
  status, and real-kernel acceptance harnesses remain the regression base.

## Non-negotiable invariants

- Every workspace-sensitive operation has explicit or captured workspace
  provenance; absence of local context never falls through to another
  workspace.
- Workspace, document, view, shell, kernel-generation, debug-session, and
  recovery identities have documented lifetimes and cannot be inferred from a
  reused filesystem path.
- Shared document content never merges workspace-local view, breakpoint,
  preference, history, or recovery state.
- Background persistence never overwrites a user's file.
- One workspace's load, migration, or recovery failure cannot block or corrupt
  another workspace.
- Every close, unload, Quit, restart, zombie, and reconciliation path is
  transactional or leaves durable recovery.
- Peer mode, legacy QtADS, and vanilla Pyzo remain deliberate supported paths.
- No stage silently expands into direct cross-workspace execution assignment,
  multiple shell views per kernel, explicit tool binding, unscoped views, or a
  new Run-as-Script spawn policy.

## Dependency map

| Stage | Depends on | Risk proof primarily retired |
|---|---|---|
| 1. Identity and context foundation | Accepted prerequisites | R1, R2 |
| 2. Shared document/view model | Stage 1 | R2, R3, R12, R13 |
| 3. Persistence, recovery, and workspace lifecycle | Stages 1–2 | R4, R5, R6 |
| 4. Execution routing and shell migration | Stages 1–3 | R7, R8, R13 |
| 5. Breakpoints, debugging, and zombies | Stages 1–4 | R6, R9 |
| 6. Tools, projects, preferences, and affiliation | Stages 1–3; accepted after Stage 5 in this queue | R10, R11, R14 |
| 7. Ingress, compatibility, scale, and final acceptance | Stages 1–6 | R14–R17 |

Stages 4 and 6 are technically separable after Stage 3, but this repository
keeps one active slice. Stage 4 precedes Stage 6 so execution provenance is
settled before tools begin consuming it.

## Ordered implementation stages

### 1. Identity and explicit workspace context foundation — **ACCEPTED 2026-07-20**

Establish the runtime ownership substrate without migrating the full config
tree or implementing shared editor content.

- Define stable runtime identities and lifetime contracts for workspace,
  document, view, shell, kernel generation, debug session, and recovery
  snapshot. Define which identities are durable and which are live-only.
- Replace the single-topology assumption with an application coordinator that
  can contain several workspace topology roots and maps every pane/view to
  exactly one workspace.
- Give workspace identity stable rename and persistence-location semantics;
  explicit copy creates a new identity and a deep, independent initial
  snapshot.
- Introduce an explicit operation/context value that resolves application,
  workspace, invoking pane/view, and resource provenance without reading focus
  again after invocation.
- Preserve application-owned commands and services, but make every
  workspace-sensitive entry point reject or explicitly handle missing context.
- Keep current single-workspace startup and behavior as the first specialization
  of the new model.
- Add focused state assertions for focus movement, pane migration, workspace
  copy/rename, missing context, and delayed callbacks.

#### Stage 1 acceptance

- Two in-memory workspace identities and topology roots coexist in one process.
- Every registered pane has exactly one owning workspace, and moving a pane
  changes only that relation and its workspace-local view state.
- Workspace rename preserves identity; copy produces a distinct identity and
  no mutable aliasing.
- Commands invoked from workspace A retain A's captured context after focus
  moves to B.
- A workspace-sensitive action with no eligible context fails visibly or uses
  an explicitly documented application-ingress rule; it never selects another
  workspace accidentally.
- Existing one-workspace peer and legacy command/lifecycle tests remain green.
- Direct-reference census records remaining global context reads and classifies
  each as application-only, captured compatibility, or a later-stage migration.

#### Stage 1 stop condition

Do not begin persisted multi-workspace migration if pane ownership, operation
context, or identity lifetime still depends on current focus, mutable path, or
object address.

#### Stage 1 completion evidence

Stage 1 introduces typed lifetime-bearing identities, a coordinator for
several topology roots, unique pane ownership, non-closing transactional pane
transfer, and captured workspace context with ownership epochs. Rename and
relocation preserve identity; copy deep-copies initial workspace state under a
new identity. The one-workspace peer startup now constructs the coordinator
and exposes its read-only collection boundary through `pyzo.application`.

Fifteen focused coordinator tests cover two simultaneous roots, duplicate
ownership, empty and absent workspace context, focus movement during command
invocation, explicit-context rejection, stale delayed context, repeated pane
migration, close/removal, rename/relocation/copy, and transfer rollback after
target rejection or backend failure. The 166-test coordinating spike suite
passes with three expected capability skips, and the nested application
controller test passes. Legacy QtADS smoke passes. Peer startup reaches and
passes the application-controller/coordinator smoke; a later pre-existing
offscreen status-projector timing assertion can still abort the long movement
replay and is recorded without expanding this slice.

The direct-reference census and exact verification commands/revisions are in
[the Stage 1 evidence artifact](../../docs/evidence/experiment-014-concurrent-workspace-implementation.md).

### 2. Shared document resources and workspace-owned views — **NEXT**

Separate document identity/content/provenance from editor-view state and prove
the model before recovery or session formats depend on it.

- Represent one document resource through views in several workspaces while
  preserving view-local cursor, selection, scroll, focus, presentation, pin,
  run highlight, and affiliation.
- Preserve shared content, dirty state, and undo semantics without duplicate
  saves or recursive signal propagation.
- Make rename and Save As preserve durable document identity and update every
  identity-based reference.
- Implement explicit branch as a new identity initialized from current content
  without later propagation.
- Extend view/document lifecycle registration so only closing the final global
  view requires Save, Discard, or Cancel.
- Make main a workspace-to-document reference independent of open views; keep
  pin as open-view state.
- Key parser and editor-derived caches by durable resource/view provenance and
  reject stale results after rename, move, branch, or close.

#### Stage 2 acceptance

- Two workspace-owned views show one shared document's live edits and dirty/undo
  state while retaining independent view state and affiliation.
- Closing or moving a non-final view never negotiates document disposition.
  Closing the final global view performs the existing transactional
  Save/Discard/Cancel path.
- Rename and Save As preserve identity, shared views, main designation, and
  cache correctness.
- Branch creates independent content identity and copies only the initiating
  workspace state explicitly required by the baseline.
- A workspace main survives closing its last view, follows rename/Save As, and
  remains visibly broken when unavailable.
- Existing clean/dirty lifecycle, editor, parser, Run-command payload, and
  recovery tests remain green.

#### Stage 2 stop condition

Do not serialize concurrent workspace documents if shared content cannot be
demonstrated independently from view state and final-view lifecycle.

### 3. Versioned persistence, recovery, and ordinary workspace lifecycle

Introduce durable workspace/process records only after identity and shared
documents are proven.

- Separate the process loaded-workspace manifest, per-workspace profile/session
  state, shared-resource references, and recovery records under explicit schema
  versions.
- Migrate the accepted single peer session into one default workspace without
  interpreting legacy named views as concurrently loaded identities.
- Preserve unknown/deprecated config and tool fields under an explicit
  round-trip policy; migrations are idempotent and retain a recoverable backup.
- Restore the same loaded workspace set and shared document relationships after
  restart. Isolate and visibly retain an unavailable workspace when only its
  record fails.
- Persist immutable workspace-local dirty snapshots without writing user files.
- Implement equality-based clean restore, divergent conflict lineages under one
  document identity, workspace-local conflict provenance, loaded-identical
  conflict propagation, and unloaded reassessment.
- Implement workspace unload/reload separately from final-view close and
  application Quit/Restart while reusing the transactional lifecycle boundary.

#### Stage 3 acceptance

- A restart round-trip restores at least two loaded workspaces, their identities,
  topology, shared document links, mains, pins/open-view state, and independent
  dirty recovery snapshots.
- Corrupting one workspace record leaves the other workspace usable and the
  failed one visibly retryable.
- Migration from the prior peer session is atomic, idempotent, and retains a
  recoverable prior-state copy.
- Workspace copy has a new identity and no mutable persistence aliases.
- No restore, unload, conflict, or recovery path writes the external user file
  without explicit Save authority.
- Content-identical retained/external versions reopen non-conflicted;
  divergence preserves both lineages and comparison metadata.
- Unloading one workspace does not dispose a shared document still viewed
  elsewhere and still captures that workspace's frozen recovery snapshot.
- Peer and legacy persistence/recovery controls remain green.

#### Stage 3 stop condition

Do not migrate ordinary user state by default until partial failure, rollback,
unknown-field preservation, and no-implicit-file-write assertions pass against
real persisted generations.

### 4. Workspace execution routing and transitional shells

Replace the application execution target with workspace-aware implicit and
view-explicit routing while preserving current Run behavior.

- Give every shell view workspace ownership and durable live identity distinct
  from kernel process generation.
- Resolve unassigned execution through the most recently foregrounded eligible
  shell in the invoking workspace, without a recency fallback queue.
- Add view-local explicit assignment, visibly broken target state, reconnect,
  and clearing back to workspace-implicit routing.
- Keep assignments live-only and preserve them across kernel recycle but not
  application restart.
- Route every small Execute command and File/Main command through one initial
  resolver; preserve current buffer/no-save behavior and Run-as-Script autosave
  plus recycle behavior.
- Implement shell movement as visible transitional state: view and new
  operations become destination-owned while the interpreter retains its current
  process state until successful recycling.
- Tag completion, help, tool, Run, and debugger requests with operation and
  interpreter-generation provenance.

#### Stage 4 acceptance

- Two workspaces can each foreground shells and run documents without
  cross-workspace fallback.
- Foreground changes affect only implicit assignments in that workspace;
  explicit assignments remain sticky.
- Unexpected target loss remains broken until reconnect or clear. Confirmed
  closure follows the accepted implicit-routing reset.
- Every Execute and Run-as-Script variant proves its invoking workspace,
  selected shell identity, kernel generation, save behavior, and recycle result.
- A moved shell remains transitional through ordinary execution, repeated move,
  source close, and failed recycle; successful recycle completes migration.
- Destination close treats the shell as destination-owned and uses normal live
  shell confirmation.
- Delayed responses from old targets or generations are rejected.
- Existing real-kernel Run, multi-kernel, shell-toolbar, lifecycle, peer, and
  legacy workflows remain green.

### 5. Workspace breakpoint overlays, debugging, and zombie lifecycle

Replace path-global breakpoint broadcast and application debugger selection
with workspace/session ownership, then extend lifecycle for surviving debug
state.

- Persist breakpoint overlays by workspace and durable document identity.
- Project independent overlays in shared-document views and send only the
  selected workspace overlay to a newly started debug session.
- Fix overlay ownership for a session while permitting ordinary live edits and
  zombie-transient edits within that ownership context.
- Copy only the branching workspace's overlay on explicit document branch.
- Retain broken inactive entries for unavailable document identities, with
  document-level discard and identity-based reactivation.
- Keep foreground-shell debugger controls and postmortem provenance; never
  redirect a non-debug shell action to another session.
- On workspace close with live debug/postmortem state, retain the minimal zombie
  workspace, its complete overlay, session context, and debugger-opened editable
  source views.
- Implement zombie retirement, dirty-view recovery, transient breakpoint
  discard, and saved/zombie/merge reconciliation on reopen.

#### Stage 5 acceptance

- Shared document views in two workspaces display and persist independent
  breakpoint overlays, and each debug session receives only its owner.
- Rename, Save As, branch, unavailable source, path reuse, recovery, and
  document-level discard preserve identity semantics.
- Existing sessions do not switch overlay owner when a shell moves; new
  sessions use the shell view's destination workspace even before recycle.
- Multiple live and postmortem sessions remain independently selectable by
  foreground shell.
- Closing a workspace with dependent sessions creates one zombie; session
  reference lifetime, temporary view ownership, and retirement match the
  requirements.
- Zombie breakpoint changes force Use Saved/Use Zombie/Merge on reopen. Live
  debugging blocks full reopen until choice; postmortem-only reopen may defer
  choice but cannot start new debugging.
- Zombie retirement captures dirty temporary views to recovery, closes clean
  views, discards unreconciled transient breakpoints, and leaks no workspace.
- Full real-kernel debugging/postmortem, lifecycle, recovery, peer, and legacy
  replays remain green.

#### Stage 5 stop condition

Do not accept zombie behavior until reference lifetime and every reconciliation
cancel/failure path have machine-checkable rollback or durable-recovery
assertions.

### 6. Tools, projects, preferences, history, and affiliation

Migrate the remaining audited contextual state after workspace identity,
persistence, and execution provenance are stable.

- Split the monolithic config through the Experiment 013 ownership census,
  preserving application-only settings and compatibility residue.
- Store requested and effective values separately when runtime capability
  forces application-wide language, theme, style, scale, or debugger mode.
- Make shell profiles, command history, starred-directory project records, and
  project options workspace-local snapshots as required.
- Allow distinct workspace-owned instances/views of each supported built-in
  tool while keeping tool code and installation application-wide.
- Make initial tool following workspace-bounded and foreground-based; show an
  inactive/empty state without an eligible local resource.
- Record a compatibility contract for third-party tools with one-instance,
  global-context, or unknown-config assumptions. Preserve undeclared data.
- Provide persistent, unobtrusive, accessible workspace affiliation for every
  pane whenever several workspaces are loaded. Do not rely on theme alone.

#### Stage 6 acceptance

- The complete Experiment 013 census has a tested final owner, copy behavior,
  live-update behavior, and compatibility treatment for every current key.
- Changing a workspace preference, project record, history, or tool-view state
  does not mutate another workspace unless an application-owned resource is
  explicitly shared.
- Snapshot copy contains no mutable aliases and does not establish later
  propagation.
- Two instances of each supported built-in tool retain independent view state
  and never follow another workspace's editor or shell.
- Capability-limited settings preserve per-workspace requests while accurately
  showing the effective application value.
- Unknown third-party config round-trips; incompatible tools fail locally and
  visibly rather than corrupting another workspace.
- Every pane exposes workspace affiliation through visible and accessibility
  state across theme, focus, movement, floating, and restore changes.

### 7. External ingress, compatibility, scale, and integrated acceptance

Close remaining boundaries and accept the complete initial model.

- Route command-line and operating-system file opens through the accepted
  most-recent available workspace rule, with default-workspace creation when
  none is loaded.
- Ensure filesystem project membership never silently chooses a workspace.
- Exercise restore and steady-state resource costs with several workspaces,
  shared documents, tools, recovery records, and an unavailable workspace.
- Replay every requirement edge across peer mode, vanilla Pyzo, and legacy
  QtADS, including application Quit/Restart and fallback behavior.
- Re-run the state/config census and direct-global-context census; classify or
  remove every remaining accidental application scope.
- Record exact coordinating, Pyzo, QtADS, and binding revisions and all accepted
  capability fallbacks.

#### Stage 7 acceptance

- External opens route deterministically under available, unavailable,
  closing, empty-loaded-set, and focus-change conditions.
- A complete restart with multiple workspaces preserves identity, shared
  resources, workspace-local state, conflicts, mains, tools, and affiliation.
- Representative scaling evidence records startup time, steady resource count,
  callback/signal behavior, and failure isolation without an unbounded trend.
- The coordinating unit/state-machine suite and full real editor, shell, tool,
  movement, lifecycle, Run/debug, postmortem, recovery, restore, multi-kernel,
  zero-frame, and shutdown replay pass.
- Vanilla Pyzo and legacy QtADS controls pass against migrated user state.
- No `QMainWindow` returns in peer startup, no workspace-sensitive operation
  uses implicit global fall-through, and no background path writes a user file.
- All deferred capabilities remain explicitly deferred or have a separately
  accepted requirement change; none enters accidentally.

## Cross-stage verification policy

Every accepted stage records:

- the identities/scopes introduced or migrated;
- the prior global/path/widget assumption removed;
- state-machine or focused unit evidence for success, cancellation, and failure;
- coordinating-suite result;
- real peer replay appropriate to the touched behavior;
- vanilla/legacy control result where shared Pyzo code changed;
- Python compilation and root/nested whitespace checks;
- direct-reference or persisted-state census deltas;
- exact root, nested Pyzo, QtADS, and binding revisions;
- any newly exposed blocker or deferred capability without silently changing
  this plan.

Each stage is committed independently after acceptance. Do not mix later-stage
migration into an earlier proof merely because the same file is open.

## Allowed write surface

- `deps/pyzo/pyzo/` source and tests required by the active stage.
- Root `spikes/peer_frames/` contracts, services, projectors, lifecycle,
  persistence, recovery, probes, and tests required by the active stage.
- Root planning, task, evidence, checklist, and ignored local handoff state.
- Temporary isolated config/recovery/test data outside the repository.

Do not change toas/rhizome implementation. Do not change QtADS or the
PySide6-QtAds binding fork unless a dependency-level blocker is first recorded
with a minimal reproduction and an explicitly bounded follow-up decision.

## Completion evidence

Completion requires all seven stage acceptance sections, the cross-stage
verification record, an updated final state/config/global-context census, full
multi-workspace real-kernel replay, vanilla and legacy controls, and exact
accepted revisions. Evidence belongs in this task and a linked
`docs/evidence/experiment-014-concurrent-workspace-implementation.md` artifact.
