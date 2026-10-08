# Experiment 014: Implement concurrent workspaces

## Status

Scope revised by the [2026-09-06 local workspace amendment](../../docs/local-workspace-scope-2026-09-06.md).
The revised Stage 2–3 retention gate is **accepted 2026-10-04** through 015–025;
see [current review](../../docs/evidence/retention-integration-2026-10-04.md).
Shared retained documents, automatic checkpoints, closed-buffer recovery,
explicit legacy choices and workspace suspend/resume are implemented and tested.

Stages 1–3 keep their historical July acceptance below. The active acceptance
contract for retention is task 015 and the September amendment, with current
evidence recorded separately. Local Stage 4 is accepted through 026–030:
Selection, assignments/correction, all Run variants, native provenance and
[integrated real-kernel workspace closure](../../docs/evidence/workspace-close-2026-10-05.md).
Task 030 corrects the earlier broad 029 sign-off and captures the missing
cancel/failure/durable teardown/same-process resume proof.
Local Stage 5 is accepted 2026-10-06 through [031](031-workspace-debugger-and-breakpoint-ownership.md):
durable overlays, independent live/PM sessions, stale frame guards, conservative
closure and fresh-process restoration. [Acceptance evidence](../../docs/evidence/workspace-debugger-2026-10-06.md)
records exact revisions and controls.
Local Stage 6 is accepted 2026-10-06 through [032](032-workspace-contextual-state-and-tools.md):
independent contextual state, ten workspace-owned built-in tools, capability
requests/effective values, extension compatibility and pane affiliation.
[Acceptance evidence](../../docs/evidence/workspace-tools-2026-10-06.md) records
all 70 census rows and exact revisions/controls. NEXT is existing Stage 7.
Stage 7's local external file-open slice is accepted 2026-10-07 through
[033](033-external-file-open-routing.md). [Evidence](../../docs/evidence/workspace-ingress-2026-10-07.md)
records deterministic dispatch, shared retained authority, actual close/empty-set
conditions and final controls. Remaining integrated compatibility, scale, census
and physical/platform acceptance stay NEXT. [034](034-native-workspace-restore-lifecycle.md)
accepts the bounded native restore lifecycle repair; its evidence retains the
pre-existing peer affinity-seed timeout as a compatibility follow-up.
Live shell migration, transitional ownership and zombie reconciliation are
deferred; visible transfer refusal and terminate-or-cancel closure apply instead.

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
- The September amendment is normative; `docs/concurrent-workspace-requirements.md`
  retains the July baseline where it does not conflict.
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
- Every close, unload, Quit, restart and external-reconciliation path is
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
| 4. Execution routing and transfer refusal | Stages 1–3 | R7, R8, R13 |
| 5. Breakpoints, debugging, and safe closure | Stages 1–4 | R6, R9 |
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

### 2. Shared document resources and workspace-owned views — **ACCEPTED 2026-07-21**

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

The 2026-09-06 local workspace amendment supersedes the final-view and
closed-buffer portions of this historical acceptance. The revised contract is
implemented incrementally by tasks 015–022; the bullets below remain dated
evidence of the July contract until that batch is accepted.

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

#### Stage 2 historical July completion evidence

The application model now separates durable document resources from
workspace-owned views. Shared text, dirty baseline, undo/redo, path,
availability, and revision are resource-owned; cursor, selection, scroll,
focus, presentation, pin, run highlight, affiliation, and workspace ownership
are view-owned. Rename and Save As preserve identity, explicit branch creates
an independent identity, and workspace mains survive zero views and retain a
broken state when unavailable.

The existing close registry accepts typed document identity and explicit
workspace/view provenance. Cross-workspace non-final closure never negotiates
disposition, while final global closure retains the transactional
Save/Discard/Cancel path. Resource/view cache tokens reject stale asynchronous
results. Peer Pyzo editors receive durable document/view identities, synchronize
current content, preflight Save As path collisions before writing, and expose
the resource service through the application controller. Parser jobs/results
are keyed by durable document identity and rejected after revision or view
epoch drift; legacy parsing remains compatible.

Fifteen focused shared-resource tests plus four parser-provenance tests cover
the accepted state matrix. The complete 181-test coordinating suite passes
with three expected capability skips. Details and remaining transitional
references are recorded in
[the implementation evidence](../../docs/evidence/experiment-014-concurrent-workspace-implementation.md).

### 3. Versioned persistence, recovery, and ordinary workspace lifecycle — **ACCEPTED 2026-07-25**

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

The amendment supersedes frozen per-workspace document snapshots, and changes
ordinary unload/reload to shared retained-document references. Versioned storage, migration, checkpoint durability, external conflict handling
and workspace suspend/resume are accepted through the October review. The
bullets below describe historical July scope; frozen snapshots are superseded.

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

#### Stage 3 historical July completion evidence

Process loaded-set state, independently versioned workspace records, shared
document references, and workspace recovery records now publish behind one
atomic manifest. Direct failure injection at record write/fsync, generation
replace, manifest write, and manifest replace preserves the prior authoritative
generation. A corrupt workspace remains unavailable and retryable while healthy
workspaces restore and can publish new generations through opaque references to
the failed record.

Legacy peer state migrates into exactly one default workspace, preserves named
views as snapshots, retains a complete backup and unknown/deprecated fields,
and is idempotent across retries and restarts. Shared document/view identities,
mains, pins, clean baselines, and undo state have a JSON-compatible transactional
round trip that performs no file saves.

Workspace recovery snapshots are immutable and workspace-owned. Content
equality, not timestamp/signature equality, determines clean restoration;
divergence retains two lineages under one document identity with timestamps and
available comparison metadata. Resolution propagates only across equivalent
loaded conflicts, while unloaded state reassesses on reload.

The ordinary lifecycle coordinator captures stable workspace/recovery state,
preserves globally shared documents, and makes unload, reload, multi-workspace
Quit/Restart composition, cancellation, stale capture, durable-write failure,
and reconstruction failure reversible. Direct byte/mtime assertions prove that
restore, conflict resolution, unload, and reload do not write external user
files.

Peer Pyzo now migrates and restores a stable workspace identity, session,
document/view references, mains, and workspace-affined compatibility recovery.
It surfaces unavailable records, refuses destructive process-level overwrite,
allows healthy workspace persistence beside an unavailable peer, and retains
the established recovery store as a compatibility boundary. A two-launch real
peer replay used one durable identity and one legacy backup; full peer and
legacy QtADS replays remained green. Exact commands and revisions are recorded
in the [Stage 3 evidence artifact](../../docs/evidence/experiment-014-concurrent-workspace-implementation.md).

### 4. Workspace execution routing and shell-transfer refusal

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
- Keep shells in their owning workspace; support rearrangement within that
  workspace and visibly refuse cross-workspace transfer. Migration is deferred.
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
- Cross-workspace shell transfer leaves owner, kernel and assignment state
  unchanged, with visible refusal. Workspace closure offers terminate or cancel
  after retention is durable.
- Delayed responses from old targets or generations are rejected.
- Existing real-kernel Run, multi-kernel, shell-toolbar, lifecycle, peer, and
  legacy workflows remain green.

#### Stage 4 historical in-progress evidence

The first independently testable slice is complete in the coordinating root.
It introduces the pure workspace-local resolver, live view/shell/operation and
kernel-generation provenance, explicit and broken assignment states, command
save/recycle policy, transitional shell ownership, and stale-result rejection.
Focused and non-Qt coordinating evidence is recorded in the
[Experiment 014 evidence artifact](../../docs/evidence/experiment-014-concurrent-workspace-implementation.md).
Live Pyzo shell registration and Run-command integration remain before Stage 4
can be accepted.

The relocated Python 3.12 venv was rebuilt and the offscreen Qt projector
tests pass in it. The complete peer smoke also passed the clean/dirty editor
lifecycle, ordinary run/live debug, post-mortem re-entry, and multi-kernel
execution-affinity checks after the projector correction. Live shell
registration and Run-command integration still require boundary review before
Stage 4 acceptance.

The 2026-09-06 projector correction removes retired-but-valid QtADS windows
from status and command projection by reconciling with the manager's live
floating-window set. Focused Qt projection tests pass 18/18 and the pure
execution-routing proof passes 9/9. The repaired Python 3.12 venv is usable,
but the host Qt 6.11 offscreen plugin currently prevents a clean real peer
smoke completion; live integration remains unaccepted.

Current October evidence: the isolated full peer and legacy application
controls pass after the retention corrections, including the unchanged Run,
live-debug, postmortem and multi-kernel workflow. That closes the reproduced
retention/focus blockers. Task 026 now accepts the first bounded live workspace
Selection slice. [October Selection evidence](../../docs/evidence/workspace-selection-2026-10-04.md)
records native shell ownership, generation/stale guards and real namespaces,
source preservation, transfer refusal and secondary closure.
[October 5 assignment evidence](../../docs/evidence/selection-assignments-2026-10-05.md)
accepts the checked view-local chooser, sticky/reconnected targets, visible broken
state/correction and a retired-connection callback guard.
[October 5 Run variants evidence](../../docs/evidence/workspace-run-variants-2026-10-05.md)
accepts every remaining editor Execute/cell/File/retained Main/script route, with
native save cancellation, Python restart and preserved IPython behavior.
[October 5 native provenance evidence](../../docs/evidence/native-provenance-2026-10-05.md)
accepts 029: exact native query/transport receipts, current source/consumer/cache
checks, real held stale replies, script successor generations and full Run/debug/
postmortem/multi-kernel controls. The earlier full Stage 4 sign-off omitted the
integrated workspace-close proof. [030 closure evidence](../../docs/evidence/workspace-close-2026-10-05.md)
now supplies real two-kernel Cancel, failed publication, fresh confirmation,
durability before termination, process exit/foreign continuity and same-process
retained resume, with bounded repairs. This completes local Stage 4 through
026–030 under the September amendment. Implementation commits precede movement
of NEXT to Stage 5;
Stage 5 owned debugger/session/breakpoint ownership and conservative closure
warnings/negotiation, Stage 6 tool/config/history isolation. Physical macOS and
Windows/Linux native validation remain unaccepted by these offscreen proofs.
The historical transitional-shell model is deferred.

### 5. Workspace breakpoint overlays, debugging and conservative closure

Replace path-global breakpoint broadcast and application debugger selection
with workspace/session ownership under the September contract.

- Persist overlays by workspace and durable document identity; project separate
  overlays in shared-document views and fix each session's overlay owner.
- Preserve rename, Move/Fork, unavailable-source and identity reactivation rules.
- Foreground debugger controls act on that shell's own live/postmortem session;
  a non-debug shell never falls through to a different session.
- Preserve source navigation and executable captured postmortem contexts with
  durable operation/session provenance and rejection of stale responses.
- Before workspace teardown, retain editing state and warn about live interpreter
  and stack loss. Offer terminate-and-close or cancel; failure leaves it intact.
- Do not create zombies, migrate live shells or reconcile saved/zombie overlays.

#### Stage 5 acceptance

Two workspaces display/persist independent overlays; each real debug session
receives only its owner's overlay. Rename/Move/Fork and unavailable sources
preserve identity. Several live/postmortem sessions remain independently
selectable by foreground shell. Cancellation and retention failure preserve
workspace topology, views and live sessions; accepted termination closes only
the addressed workspace after durable retention. Full real-kernel debugger,
postmortem, lifecycle, peer and legacy controls remain green.

#### Stage 5 completion — 2026-10-06

[031](031-workspace-debugger-and-breakpoint-ownership.md) accepts the full local
September Stage 5 contract. [Evidence and logs](../../docs/evidence/workspace-debugger-2026-10-06.md)
record 481 coordinated tests/51 subtests, all 15 live controls and full peer/legacy
smokes; two actual independent live and executable PM contexts; fixed session
snapshots; stale frame actions/results/queries; visible stack-loss warnings;
Cancel/failure/fresh retry; overlays/text/undo/views on disk before A-only
termination with B PM continuity; retained resume and fresh-process restoration.
Identity/availability/Fork and shared edit/undo assertions pass. Implementation
commits precede this acceptance and movement of NEXT to Stage 6. File Move/Fork
UX stays separate; physical/platform acceptance remains Stage 7 debt.

#### Stage 5 stop condition

Do not accept workspace debug isolation or termination until target provenance,
cancel/failure preservation and teardown ordering have machine-checkable
assertions and real-kernel evidence. Zombie behavior is deferred scope.

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

#### Stage 6 accepted — 2026-10-06

[Task 032](032-workspace-contextual-state-and-tools.md) and
[accepted evidence](../../docs/evidence/workspace-tools-2026-10-06.md) resolve
C01–C30/P01–P06/L01–L34 in the [final census](../../docs/evidence/workspace-context-census-2026-10-06.md).
Private preferences, projects, shell profile snapshots, command history and all
ten built-in instances pass independent-state and deep-copy assertions. Native
A/B kernels prove local following, local-empty behavior, held stale reply refusal,
Cancel/failure preservation, retained close/reopen and complete fresh-process
state restoration. Explicit requested/effective application/interpreter fallbacks
and unknown extension config/refusal pass. Every pane has visible/accessibility
affiliation across owner rename, focus, native movement/floating and restore.

501 coordinated tests/56 subtests, all 16 live controls and full peer/legacy
smokes pass; 29 touched Python sources pass compile/Ruff F/whitespace. Root
`b985fa0a920e522a4c4e1750b649843e5cdc0c3d` and Pyzo
`6544d31cd7d3562856a57c242f7fd9ea254910db` implementation commits precede this
acceptance and NEXT movement. Binding unchanged. Physical macOS/platform,
vanilla upstream, scale, external ingress and the final direct-global census
remain Stage 7. File Move/Fork UX remains separate; September deferrals persist.

### 7. External ingress, compatibility, scale, and integrated acceptance

Close remaining boundaries and accept the complete initial model.

The local external file-open boundary is accepted through
[033](033-external-file-open-routing.md) and its
[2026-10-07 evidence](../../docs/evidence/workspace-ingress-2026-10-07.md).
[034](034-native-workspace-restore-lifecycle.md) and its
[native lifecycle evidence](../../docs/evidence/native-restore-2026-10-07.md)
accept detached-container revalidation and retired callback guards. The full
stage remains open, including the pre-existing peer affinity-seed timeout;
earlier broad peer-smoke success claims are corrected there. No full census/
platform/scale claim follows from the passing local replay.

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

Completion is evaluated against the September amendment and the reconciled
acceptance criteria. Deferred migration/zombie behavior in historical sections
is not a completion gate. Earlier acceptance evidence must remain dated and
must not be relabeled as proof of the new contract.

Completion requires all seven stage acceptance sections, the cross-stage
verification record, an updated final state/config/global-context census, full
multi-workspace real-kernel replay, vanilla and legacy controls, and exact
accepted revisions. Evidence belongs in this task and a linked
`docs/evidence/experiment-014-concurrent-workspace-implementation.md` artifact.
