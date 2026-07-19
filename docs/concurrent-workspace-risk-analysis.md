# Concurrent workspace risk analysis

Date: 2026-07-19

## Status and scope

This is the technical risk analysis requested before concurrent-workspace
implementation. It compares the accepted
[requirements baseline](concurrent-workspace-requirements.md) with the observed
current-state contracts in the
[Experiment 013 audit](evidence/experiment-013-workspace-state-ownership-audit.md).

The ratings describe technical exposure, not task priority or implementation
order. The analysis assigns no work and changes no product requirement.

## Executive conclusion

The concurrent-workspace model remains feasible, but it is not primarily a
configuration-namespacing change. The current system has one service registry,
one topology, one active editor, one active shell, one execution target, one
tool instance per tool ID, and document state largely embodied by one editor
widget. The accepted model instead requires an explicit identity graph joining
process, workspace, view, document, shell, kernel, debug session, and recovery
state.

Five risks dominate the feasibility boundary:

1. making workspace context explicit without leaving global fall-through paths;
2. defining durable identities and references before persistence is split;
3. separating shared document content from workspace-owned editor views;
4. migrating the monolithic persisted state without losing legacy user data;
5. extending lifecycle and recovery transactions to unloaded and zombie
   workspaces without silent data loss.

Breakpoint overlays, debugger provenance, and transitional shells are tightly
coupled to those foundations. Tool multiplicity is broad and partially
open-ended, but its initial workspace-bounded foreground-following rule reduces
the semantic risk. Theme and language independence are not feasibility gates
because the accepted application-wide fallback is explicit.

A config-first migration would have high rework risk: most config consumers
currently discover context through global current-editor/current-shell state,
so merely storing values per workspace would not establish which workspace a
read or write belongs to.

## Rating method

- **Critical**: can cause user-data loss, wrong-workspace execution, or an
  architectural dead end across several subsystems. The relevant invariant
  needs direct evidence before broad state migration depends on it.
- **High**: likely to create incorrect cross-workspace behavior, compatibility
  regressions, or extensive rework, but is containable behind a defined
  boundary.
- **Medium**: consequential but locally bounded, capability-dependent, or
  covered by an accepted fallback.
- **Low**: mechanically broad but semantically clear, or already isolated by
  the accepted peer-frame architecture.

Likelihood statements are relative to the current code described by Experiment
013. They are not calendar or effort estimates.

| Rating | Risks | Dominant consequence |
|---|---|---|
| Critical | R1–R6, R9 | Wrong-workspace action, data loss, or an identity/persistence dead end |
| High | R7–R8, R10–R11, R13–R14, R16–R17 | Cross-scope behavior, compatibility failure, or broad rework |
| Medium | R12, R15 | Bounded state error or unmeasured scale cost |

## Risk register

### R1 — Implicit global context survives the workspace split

**Rating:** Critical; likelihood high.

**Exposure:** Application singletons and active-context selectors currently
serve nearly all consumers. The audit found one process-wide service set and
one active pane/editor/shell (`L01`, `L02`, `L04`, `L07`, `L17`, `L18`). A
focused source count finds `pyzo.config` in 26 core/tool files,
`pyzo.editors` in 16, and current-editor/current-shell access in 28 files.

**Failure modes:**

- a command reads or writes the foreground workspace instead of the invoking
  view's workspace;
- a delayed callback changes behavior after focus moves;
- tools follow activity in another workspace;
- application-level commands accidentally require a current workspace;
- status, dialogs, metadata, or shortcuts project correct chrome but execute
  against the wrong owner.

**Risk-reduction evidence:** Every workspace-sensitive operation can be traced
from an invoking view, explicit workspace identity, or captured operation
context. Application-only operations are explicitly classified. Tests cover
focus changes between invocation and completion and prove that absence of local
context does not fall through to another workspace.

### R2 — Durable identity and reference graph is underspecified in current code

**Rating:** Critical; likelihood high.

**Exposure:** Current document handles are a live `FileItem.lifecycleId`, a
path-or-temporary editor ID, and recovery IDs with different lifetimes (`L09`,
`P04`). Save As changes a path-based ID. Shells and shell profiles also lack
stable persisted identity (`C20`, `L16`, `L22`). The current peer session has no
workspace identity and records only one topology (`C06`).

**Failure modes:**

- rename or Save As silently severs main, breakpoint, recovery, parser, or run
  assignment references;
- two paths alias one document or one reused path aliases the wrong document;
- branch and conflict lineages are confused;
- restore duplicates a shared document instead of reconnecting its views;
- a broken shell assignment reconnects to a different shell;
- workspace copy accidentally preserves source identity.

**Risk-reduction evidence:** A single documented identity/lifetime table covers
workspace, document, content lineage, view, shell, kernel, debug session, and
recovery snapshot. Serialization round-trips references across rename, Save As,
branch, workspace copy, unload/reload, partial restore failure, and path reuse.
Identity recovery never relies on path equality alone.

### R3 — Shared document content is not separated from editor-view state

**Rating:** Critical; likelihood high.

**Exposure:** Pyzo currently models one `FileItem` around one editor widget, and
filename, dirty state, content, cursor-facing behavior, breakpoints, parser
keys, provenance, and close behavior meet at that widget (`L09`–`L15`). The
lifecycle registry can represent several views, but the editor integration
registers only one view per `FileItem` (`L26`).

**Failure modes:**

- supposed shared views receive duplicate buffers and diverge accidentally;
- sharing a Qt document also shares state that should remain view-local;
- undo, cursor, scroll, parser, indicator, and dirty-state signals are delivered
  to the wrong view;
- one workspace closes or saves the resource while another still depends on
  it;
- branch creation shares mutable state that should have been copied;
- an external-file reload or Save As races several views.

**Risk-reduction evidence:** A focused multi-view proof demonstrates one shared
content/dirty/undo resource with independent cursor, selection, scroll, focus,
presentation, pin, and workspace affiliation. It also demonstrates final-view
closure, rename, Save As, explicit branch, external modification, and recovery
without duplicate saves or signal loops.

### R4 — Persistence split and legacy migration can corrupt or strand state

**Rating:** Critical; likelihood high.

**Exposure:** One recursive SSDF object mixes application preferences,
workspace candidates, session topology, tools, shell profiles, and
compatibility residue (`C01`–`C30`). `state.peerWorkspaceSession` represents one
replaceable topology; named views are snapshots, not concurrently loaded
identities (`C06`, `C07`). Third-party tools may add arbitrary unseen keys
under `tools.<toolId>` (`C22`).

**Failure modes:**

- the first new-version save makes older data unrecoverable;
- partial workspace corruption prevents process restore;
- copied workspaces share mutable SSDF subtrees;
- legacy named views are mistaken for workspace identities;
- application-only settings are duplicated and later disagree;
- unknown tool data is dropped, globally shared unintentionally, or copied with
  unsafe semantics;
- a crash commits a process manifest that references incomplete workspace
  records.

**Risk-reduction evidence:** The persisted model is versioned, atomic, and
reference-aware; process loaded-set state is separate from per-workspace state;
one failed workspace is quarantined without blocking others; copy is deep and
creates a new identity; migrations are idempotent; backups permit recovery;
unknown and deprecated fields have an explicit round-trip policy.

### R5 — Recovery and conflict semantics exceed the current recovery model

**Rating:** Critical; likelihood high.

**Exposure:** The current recovery store already has atomic generations,
immutable records, quarantine, disk signatures, and an unused
`workspace_affinity` field (`P04`). However, retention currently occurs at
application exit; workspace unload, frozen per-workspace snapshots, shared
document lineages, conflict equivalence, and loaded-only resolution propagation
do not exist (`L10`, `L28`). Conflict is presently little more than a restored
marker.

**Failure modes:**

- background recovery overwrites a user file;
- another workspace's save erases or mutates a closed workspace's snapshot;
- identical recovery is presented as a conflict or divergent recovery is
  accepted silently;
- resolving one workspace incorrectly resolves an unloaded workspace;
- conflict lineages are assigned new document identities implicitly;
- Save, Discard, or workspace closure retires recovery still needed elsewhere.

**Risk-reduction evidence:** State assertions cover snapshot creation,
immutability, equality-based no-conflict restore, divergent restore, explicit
save authority, branch/merge outcomes, loaded identical-conflict propagation,
unloaded reassessment, and final-view retirement. Every failure path preserves
at least one recoverable copy and never writes the external file implicitly.

### R6 — Workspace close, zombie lifetime, and application exit form one state machine

**Rating:** Critical; likelihood medium-high.

**Exposure:** Existing lifecycle coordinators already provide transactional
document/shell close and application shutdown (`L26`, `L27`), which is a useful
base. They do not model workspace unload or a zombie owner. The accepted
requirements add loaded, closing, unavailable, zombie, reopening, reconciled,
and retired workspace states, with temporary editable views and session-based
zombie lifetime.

**Failure modes:**

- closing a workspace terminates a debugger that should keep a zombie alive;
- a zombie leaks after its last dependent session;
- a temporary view keeps a zombie alive contrary to the contract;
- retiring a zombie drops a dirty buffer or persists transient breakpoints;
- application Quit, workspace Close, final-view Close, and shell Close bypass
  one another's negotiations;
- reopening creates a second workspace object with the same identity;
- failed or cancelled reconciliation leaves two semantic owners.

**Risk-reduction evidence:** A machine-checkable transition table covers every
workspace state and event, with explicit ownership and rollback assertions.
Reference counts include debug/postmortem sessions but exclude temporary views.
Quit and restart compose the same workspace transactions rather than bypassing
them. Reopen, reconciliation cancellation, recovery failure, and zombie
retirement are all reversible or leave durable recovery.

### R7 — Execution routing can target a valid but wrong shell

**Rating:** High; likelihood high.

**Exposure:** Current Pyzo has one `_activeHost` and one `_executionHost`; host
removal silently falls back to another host (`L17`, `L18`). Run variants and
debug controls currently resolve that application target (`L31`, `L32`). The
accepted behavior instead combines invoking workspace, workspace implicit
target, view-local explicit assignment, foregrounding, broken-target state,
and command-specific recycling.

**Failure modes:**

- code executes successfully in another workspace's shell;
- a dead target silently selects an older shell;
- foreground focus changes explicit assignment;
- corrective choice changes only one view when workspace scope was intended;
- Run as Script recycles the wrong kernel;
- delayed completion or introspection is accepted after a view migrates.

**Risk-reduction evidence:** A resolver truth table covers each command kind,
invoking view kind, explicit/implicit/broken state, shell eligibility, focus
change, shell death, confirmed closure, and restart. Resolution returns an
explicit provenance object rather than a bare current shell, and asynchronous
results validate that provenance before projection.

### R8 — Transitional shell semantics split view, operation, process, and debug ownership

**Rating:** High; likelihood medium-high.

**Exposure:** A moved shell view becomes destination-owned immediately, new
operations use destination preferences and breakpoints, the live interpreter
retains source-created process state, an existing debug session retains its
original overlay, and only recycling completes migration. Current shell,
connection, kernel, and view are effectively one-to-one (`L16`, `L19`, `L22`).

**Failure modes:**

- UI reports migration complete while the process still has source provenance;
- new and existing debug sessions use the same mutable breakpoint set;
- source or destination closure destroys the wrong state;
- failed recycling leaves contradictory ownership;
- a shell restarts with the wrong profile, project path, environment, or cwd;
- command enablement follows process provenance instead of view ownership.

**Risk-reduction evidence:** Shell state exposes separate immutable identifiers
for view owner, interpreter generation, operation context, and debug-session
overlay. A transition matrix covers move, repeated move, source close,
destination close, ordinary execution, new debugging, active debugging,
recycle success/failure, and application restart. Transitional affiliation and
correction are observable in both chrome and accessibility state.

### R9 — Workspace breakpoint overlays conflict with the current global broadcast model

**Rating:** Critical; likelihood high.

**Exposure:** Breakpoints currently live in editor block metadata, are
aggregated by path, and are broadcast to every live shell; they are not durable
(`L15`). Debug indicators are also projected from one selected debugger
(`L23`, `L24`). The accepted model requires persistent workspace overlays,
per-session snapshots, unavailable-source entries, branch copying, zombie
transience, and saved/zombie/merge reconciliation.

**Failure modes:**

- kernels receive breakpoints from the wrong workspace;
- one view's breakpoint edit changes another workspace;
- rename, Save As, branch, or path reuse binds breakpoints incorrectly;
- a running debugger switches to another workspace's overlay mid-session;
- zombie edits silently become durable or are silently lost during reopen;
- merging overlays produces duplicate or stale line entries.

**Risk-reduction evidence:** Breakpoints are keyed by workspace and durable
document identity, never path alone. A debug session fixes its overlay owner at
start; ordinary and zombie-transient edits are delivered only within that
selected ownership context. Tests prove independent simultaneous overlays,
branch copying, unavailable-source reactivation/discard, ownership stability,
zombie editing, all three reconciliation outcomes, and
deferred-reconciliation debug blocking.

### R10 — Tool multiplicity is partly unknowable from the checked-out source

**Rating:** High; likelihood high for built-ins, unknown for third-party tools.

**Exposure:** `ToolManager._activeTools` is keyed only by tool ID and returns an
existing instance when the same tool is loaded again. Most tools read one
global config subtree and follow global current editor/shell state (`C04`,
`C22`–`C30`, `L25`). Third-party tool schemas and singleton assumptions cannot
be enumerated in advance.

**Failure modes:**

- loading a tool in a second workspace merely focuses or steals the first
  instance;
- view-local navigation and workspace preferences overwrite each other;
- a tool follows a resource in another workspace;
- user tools rely on one global instance or mutate module globals;
- unknown config is duplicated even though it names an application-shared
  library or credential.

**Risk-reduction evidence:** Every built-in tool has an instance-capability and
state-ownership record. Manager keys distinguish tool type from tool-view
identity and workspace. Resource following is workspace-bounded and becomes
inactive without a local resource. Legacy third-party tools have an explicit
compatibility mode and unknown config is preserved until its ownership is
declared.

### R11 — Preference splitting is broad and reference aliasing can defeat snapshots

**Rating:** High; likelihood high.

**Exposure:** The audit classifies 115 default entries, 25 dynamic built-in
keys, and open-ended extension keys. Consumers read the recursive global config
directly. Some live objects retain references to mutable config structs; shell
profiles are the most consequential example (`C20`). Command history and tool
libraries also mix application and candidate workspace scope (`P01`–`P03`).

**Failure modes:**

- changing workspace A mutates a structure still referenced by B;
- snapshot copy remains linked to its source;
- live widgets cache a prior workspace's setting;
- application-only scale, shortcuts, or installation state is duplicated;
- effective capability fallback overwrites the workspace's requested value.

**Risk-reduction evidence:** Every audited key has one declared storage owner,
effective owner, copy behavior, and live-update behavior. Snapshot copy is
structurally independent. Requested and effective values are distinct where
capability can force fallback. Compatibility fields round-trip without gaining
accidental workspace semantics.

### R12 — Main-file and pinned-view state currently depend on an open host and mutable path ID

**Rating:** Medium; likelihood high.

**Exposure:** Main is stored per `FileTabWidget` as an item ID, manager lookup
searches open hosts, Save As can change the item ID without updating the stored
main, and persistence embeds main/pin markers in the open-editor list (`C03`,
`L12`, `L33`). The accepted model makes main a closed-capable workspace
designation while pin remains open-view state.

**Failure modes:**

- closing the main view clears or strands the designation;
- Save As or rename makes Execute Main fail;
- two workspaces accidentally share one main marker;
- path reuse runs a different document;
- restoring a main reopens it merely to reconstruct designation state.

**Risk-reduction evidence:** Main is stored as a workspace-to-document-identity
reference separate from open views. Rename, Save As, close-last-view, missing
file, relocate, choose-another-main, workspace copy, and Execute Main from
different pane types all preserve the accepted semantics. Pin state remains on
an open view only.

### R13 — Asynchronous caches and responses carry mutable global provenance

**Rating:** High; likelihood medium-high.

**Exposure:** Parser caches are keyed by mutable editor ID, completion and
calltip work combines editor/parser/current-shell state, and response validity
checks use global current editor/current shell (`L14`, `L21`). QtADS projection
also deliberately performs queued reconciliation (`L03`). Multiple loaded
workspaces increase the chance that focus or ownership changes while work is in
flight.

**Failure modes:**

- stale completion, help, parser, or debugger results appear in another view;
- Save As leaves cache entries under the old identity;
- moving a view accepts a response from its former workspace or shell;
- queued backend activation overwrites a newer semantic selection;
- teardown callbacks act on recycled identities.

**Risk-reduction evidence:** Requests and caches carry durable document/view,
workspace, shell, and interpreter-generation provenance as applicable. Results
are rejected or rerouted when provenance no longer matches. Tests force focus,
rename, migration, closure, and recycling between request and response.

### R14 — Required state visibility can lag behind semantic state

**Rating:** High; likelihood medium-high.

**Exposure:** Current status is one snapshot mirrored into every frame (`L06`),
and command projections mix application definitions with global context (`L07`).
The requirements depend on users being able to distinguish workspace owner,
broken main, broken assignment, unavailable workspace, transitional shell,
zombie view, and pending breakpoint reconciliation.

**Failure modes:**

- behavior is technically correct but appears to target another workspace;
- a disabled action has no explanation or corrective path;
- color/theme is the only affiliation signal and fails under global fallback or
  accessibility needs;
- queued projection leaves dangerous commands briefly enabled;
- a zombie or transitional shell appears ordinary.

**Risk-reduction evidence:** Each semantic exceptional state has persistent
text/icon/accessibility representation independent of theme. Command labels,
enabled state, explanations, and corrective actions derive from the same state
object as execution. Multi-frame tests verify settled projection after focus,
move, close, failure, and reconciliation events.

### R15 — Restore and runtime scaling are unmeasured

**Rating:** Medium; likelihood unknown.

**Exposure:** Current startup restores one topology, one tool instance per ID,
and no shared multi-view document graph. Several workspaces multiply topology,
tool, parser, view, status, and persistence activity even when document and
kernel resources are shared.

**Failure modes:**

- startup becomes dominated by eagerly constructing every workspace's tools
  and views;
- restore signal storms select the wrong active context;
- duplicated caches defeat the intended benefits of shared resources;
- large atomic manifests become slow or fragile;
- unavailable workspaces repeatedly delay normal startup.

**Risk-reduction evidence:** Representative restore measurements cover several
workspaces, shared documents, tools, unavailable entries, and recovery records.
Resource counts and signal/callback counts remain bounded, and one failed
workspace does not extend the critical path for successful workspaces beyond a
defined isolation cost.

### R16 — Legacy and platform fallback regressions can hide behind peer-mode success

**Rating:** High; likelihood medium.

**Exposure:** The accepted peer startup now has no `QMainWindow`, while vanilla
Pyzo and legacy QtADS remain valuable fallbacks. Configuration and services are
still shared code. Theme/language/Qt style and shortcuts have application or
platform boundaries (`C14`, `C15`, `C19`, `L30`). Third-party tools also rely on
the existing public singleton surface.

**Failure modes:**

- workspace-aware APIs break vanilla single-workspace Pyzo;
- migration makes old config unreadable or discards compatibility fields;
- a peer-only context assumption disables legacy toolbars or menus;
- macOS application-menu success masks Windows/Linux projection failures;
- capability fallback stores an effective value over a user's request.

**Risk-reduction evidence:** Every accepted slice continues to exercise peer
mode, legacy QtADS, and vanilla fallback against the same user-state migration.
Single-workspace behavior remains a specialization of the multi-workspace
model, and platform/capability differences are represented explicitly rather
than inferred from the foreground view.

### R17 — The state-space can outgrow example-based tests

**Rating:** High; likelihood high.

**Exposure:** Experiment 013's 88 focused tests establish strong current
transactional seams, but they exercise one application workspace. The new
model combines workspace load state, document sharing and dirty state, view
count, shell liveness, assignment, migration, debug mode, zombie lifetime,
recovery conflict, and reconciliation.

**Failure modes:**

- happy paths pass while event ordering violates an invariant;
- cancellation and partial failure leave half-committed ownership;
- fixes for one close route bypass another route;
- a rare combination silently drops recovery or targets the wrong kernel.

**Risk-reduction evidence:** Core identity, lifecycle, recovery, routing,
breakpoint, and zombie contracts have model/state-machine tests in addition to
scenario replays. Assertions check ownership uniqueness, reference validity,
transaction rollback, no implicit file writes, and no cross-workspace fallback
after every transition.

## Risk interactions

The risks are not independent:

- **R1 + R2 + R3** form the runtime ownership foundation. Context cannot be
  reliable without stable identities, and stable identities do not provide
  shared documents until view state is separated from content.
- **R2 + R4 + R5** form the durable identity/recovery foundation. Persisting
  workspaces before references and conflict lineages are stable risks encoding
  a migration dead end.
- **R1 + R7 + R8 + R13** govern execution safety. A bare shell pointer is not
  enough once view ownership, interpreter generation, and operation provenance
  can differ.
- **R2 + R5 + R6 + R9** govern zombie correctness. Zombie breakpoint
  reconciliation is unsafe without durable document identity and transactional
  recovery.
- **R1 + R10 + R11** govern scope leakage. Duplicating tool instances or config
  objects does not prevent cross-workspace following when consumers still read
  global context.
- **R14 + every routing/lifecycle risk** is a safety multiplier: silent or
  ambiguous UI turns a recoverable semantic transition into apparent data loss
  or execution in the wrong environment.

## Existing seams that reduce risk

The current branch is not starting from an unstructured application:

- peer mode has a non-window application controller and application-owned
  command descriptors;
- pane identity and topology already have a structured model/backend split;
- document and shell lifecycle registries already negotiate final-view and
  live-shell closure transactionally;
- application shutdown already separates negotiation, cleanup, and committed
  exit;
- recovery already uses immutable records, atomic generations, quarantine, and
  disk signatures;
- peer session capture/restore already has validation and rollback;
- shell host identity already survives kernel recycling in the current live
  process;
- command and status projection already centralize much of the chrome that
  will need workspace-aware state.

These seams reduce construction risk, but none currently supplies concurrent
workspace identity. Treating their present “workspace” names as proof of that
identity would increase risk.

## Scope reductions already accepted

The following decisions materially contain risk:

- single-workspace behavior remains valid rather than requiring separate code;
- kernels are not restored across application restart;
- direct cross-workspace assignment and extra shell views per kernel are
  deferred;
- tools initially follow only the foreground eligible resource in their own
  workspace, with no explicit binding algorithm;
- Run as Script keeps the existing recycle behavior;
- shortcut mapping, scale factor, installation, and other true process
  capabilities may remain application-wide;
- theme and language may remain application-wide when independent application
  is unsupported;
- unscoped views are excluded;
- conflict-resolution history need not persist after resolution;
- per-breakpoint discard of unavailable-source entries is not required.

## Proof obligations before broad dependence

These are evidence requirements, not assigned tasks or execution order:

1. **Identity proof:** stable identities and serialized references survive all
   accepted rename, branch, copy, unload, restart, and path-reuse cases.
2. **Shared-document proof:** two workspace-owned views share content while
   retaining independent view state and correct final-view lifecycle.
3. **Context proof:** commands, tools, delayed callbacks, status, and ingress
   cannot fall through to another workspace.
4. **Durability proof:** versioned migration and partial restore preserve legacy
   state, unknown tool fields, unavailable workspaces, and recoverable dirty
   content atomically.
5. **Lifecycle proof:** close, unload, Quit, restart, zombie, reopen, and
   reconciliation form one rollback-safe transition system.
6. **Execution proof:** implicit, explicit, broken, transitional, recycled, and
   debug-session routing have machine-checked target provenance.
7. **Breakpoint proof:** independent durable overlays and fixed session-overlay
   ownership remain correct through shared documents, branches, live edits,
   zombies, and reconciliation.
8. **Compatibility proof:** peer, vanilla, and legacy QtADS paths continue to
   pass the relevant lifecycle, command, persistence, and debugger workflows.

## Open implementation-analysis questions

The product semantics are settled, but the following technical choices still
carry risk:

- Can the current Pyzo editor safely project one shared content/undo resource
  through several editor widgets, or does it require a separate document model?
- What durable identifier and reference format covers pathless documents,
  branch lineages, workspace copies, live shells, and recovery without path
  aliasing?
- How should versioned process-session, workspace-profile, shared-resource, and
  recovery records be divided while retaining atomicity and legacy import?
- Which existing services become workspace-owned instances, and which remain
  application services that require explicit workspace context?
- What compatibility contract applies to third-party tools that assume one
  instance, one config subtree, and global current editor/shell access?
- How are asynchronous parser, completion, tool, and debugger responses tagged
  and cancelled when views move, close, rename, or change execution target?
- How are ordinary live breakpoint edits and zombie-transient breakpoint edits
  delivered to an active kernel without changing the session's selected
  workspace overlay?
- What is the storage cadence for silent workspace recovery snapshots inside a
  running application?
- How are application-level status messages composed with workspace-local
  status without one obscuring the other?
- Which interpreter capabilities can actually support independent debugger
  selection, and how is the effective shared mode reported?
- What representative workspace/document/tool scale should define acceptable
  restore and steady-state resource cost?

None of these reopens the accepted product model. They identify the technical
evidence needed to avoid encoding accidental current-state assumptions into the
implementation.
