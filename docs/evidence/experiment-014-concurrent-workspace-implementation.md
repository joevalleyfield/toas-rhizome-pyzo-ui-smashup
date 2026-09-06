# Experiment 014 implementation evidence

## Stage 1 — identity and explicit workspace context

Accepted on 2026-07-20.

### Delivered substrate

- `ApplicationIdentity` separates identity from path, display name, object
  address, and mutable persistence location.
- Workspace, document, view, and recovery-snapshot identities are durable;
  shell and debug-session identities are live-session scoped; kernel generation
  is generation scoped.
- `WorkspaceCoordinator` owns multiple simultaneous topology roots and rejects
  duplicate pane ownership across them.
- Workspace rename and relocation retain identity. Copy creates a fresh
  workspace identity and a deep, independently mutable initial state snapshot.
- Pane transfer is transactional and non-closing. Descriptor and close policy
  move together, both topology roots roll back on source/backend/target failure,
  and successful transfer leaves placement to a later workspace-local UI step.
- `ActiveContext` captures workspace, pane, group, frame, and ownership epoch.
  Missing or mismatched explicit context never falls through to the currently
  active workspace. Ownership epochs make delayed context stale after move,
  repeated move, close, or workspace removal.
- Peer startup remains a one-workspace specialization but creates the
  coordinator, routes the command registry through it, registers panes through
  its process-wide ownership gate, and exposes a read-only workspace collection
  from the application controller.

No document sharing, persisted multi-workspace format, recovery migration,
execution routing, breakpoint overlay, tool preference split, or user-data
migration is part of this stage.

### State and failure coverage

The 15 focused coordinator tests cover:

1. all identity kinds and lifetime classifications;
2. no-workspace versus empty-workspace context;
3. two simultaneous roots and exactly-one pane ownership;
4. command capture in workspace A followed by focus activation in B;
5. absent and mismatched explicit context with no fallback;
6. stale context after transfer, repeated transfer, close, and removal;
7. coordinator duplicate registration rejection and invariant detection of a
   direct-model bypass;
8. non-closing transfer with policy preservation;
9. atomic rollback when a target mutates and then rejects;
10. atomic rollback when backend publication fails;
11. rejection of stale backend activation;
12. stable rename/relocation and deep-copy isolation; and
13. invalid operations leaving active context and ownership unchanged.

### Direct-reference census

The Stage 1 scan used:

```sh
rg -n 'getCurrentEditor|getCurrentShell|getExecutionShell|resolve_active_context|pyzo\.editors|pyzo\.shells|_peerWorkspace' \
  deps/pyzo/pyzo --glob '*.py'
```

Remaining reads are classified as follows:

| Classification | Current sites | Planned treatment |
| --- | --- | --- |
| Application-only registry/lifecycle | `_start.py`, parser notification, application shutdown iteration, editor/shell group installation | Retain the process-wide resource registries; workspace-sensitive consumers must not infer ownership from registry membership. |
| Captured compatibility boundary | `applicationController.py`, `runCommands.py`, `shellCommands.py`, existing command projections | The new controller context is captured now. Execution-shell/editor compatibility remains intentionally single-workspace until Stage 4. |
| Stage 2 document/view migration | `editor.py`, `editorTabs.py`, `editorGroups.py`, document actions in `menu.py`, file-browser/editor-list/source-structure/snippet consumers | Replace current-editor inference with workspace-owned view/document provenance. |
| Stage 4 execution migration | `runCommands.py`, `shellCommands.py`, `shell.py`, `shellStack.py`, execution-target portions of `menu.py` and runner examples | Route with captured workspace/view assignment and the accepted sticky shell rules. |
| Stage 5 debug migration | breakpoint/debug reads in `shell.py`, `shellStack.py`, `editor.py`, and debug portions of `main.py` | Add workspace breakpoint overlays and debug-session provenance. |
| Stage 6 tool/preference migration | history, workspace, expression, file-browser, interactive-help, snippets, editor-list, and source-structure tools | Give tools accepted workspace affiliation/following semantics. |
| Transitional peer integration | direct `_peerWorkspace` uses in `main.py` | The default root remains the one-workspace compatibility specialization; migrate each lifecycle/layout call to explicit coordinator ownership as its dependent stage lands. |

The Stage 1 delta removes ambient focus from the application command context
resolver and places actual peer pane registration behind the process-wide
coordinator. The census deliberately remains nonzero; later rows are explicit
stage obligations rather than claims of workspace safety.

### Verification

- `python -m unittest discover -s spikes/peer_frames -p 'test_*.py'` under the
  bundled Python 3.12/PySide6 runtime: **166 passed, 3 expected skips**.
- Focused identity/coordinator suite: **15 passed**.
- Focused command/contract/coordinator suite: **46 passed**.
- Nested `test_application_controller.py` controller-boundary test: **passed**.
- Python 3.12 compilation of all touched root and nested Python files:
  **passed**.
- Root and nested `git diff --check`: **passed**.
- Legacy QtADS offscreen replay with configuration saving disabled: foreground
  ordering, independent editor docks, debugger routing, tool containers,
  dual-layer guides, shell toolbar enablement, independent shell docks, and
  command-server shutdown all **passed**.
- Peer offscreen replay with the local four-side binding: independent editor
  docks, the new application-controller/coordinator assertion, debugger routing,
  tool containers, native overlay ownership, shell toolbar enablement,
  workspace-session round trip, and the real-pane movement matrix all
  **passed before** a later status-projector/live-window timing assertion.

The peer replay's later `_testCleanPeerEditorLifecycle` assertion compares
projected status-window IDs immediately after asynchronous frame retirement.
It is outside the coordinator/context changes and occurred after the Stage 1
smoke assertion passed. It is retained as a follow-up candidate rather than
silently fixed or used to widen this stage.

### Accepted revision baseline

- Root before Stage 1 commit: `01284ba39cf2e277c52676fa2b099a56b53f70e1`
- Nested Pyzo before Stage 1 commit: `b3af8d98795b50e6f8b31f263b163552dc0c6ef5`
- Accepted nested Pyzo Stage 1 revision:
  `c2903fc7467c0ebe24fab13c8235715cf3477b2f`
- PySide6-QtAds binding used by peer control:
  `764eb4a487abccb162dcbee1a8f0383916561e0e`

The accepted nested revision is recorded below before the root evidence commit.
The root Stage 1 revision is the commit containing this artifact and is also
reported in the local handoff and completion response, avoiding a recursive
self-reference inside the commit itself.

## Stage 2 — shared documents and workspace-owned views

Accepted on 2026-07-21.

### Delivered substrate

- `DocumentResourceRegistry` owns typed durable document identities separately
  from paths and typed durable view identities separately from editor widgets.
- A shared resource owns live text, clean/dirty baseline, undo/redo history,
  revision, path, availability, and lifecycle. Workspace views independently
  own cursor, selection, scroll, focus, presentation, pin, run highlight,
  affiliation, and workspace identity.
- One logical edit or undo/redo changes the resource once and notifies every
  view once. No-op edits do not add history, and recursive signal propagation
  is rejected.
- Moving a view changes workspace identity and view epoch without changing
  resource identity, text, dirty state, history, or view-local state.
- Rename and Save As preserve document identity. Cancel, failure, exception,
  and collision leave the complete model snapshot unchanged. Peer Pyzo checks
  path ownership before writing and adopts a successful foreground save
  without performing a duplicate write.
- Explicit branch creates a new identity/resource/view from current content
  and a deep copy of the initiating view state. Subsequent content and undo
  history are independent.
- Workspace main is a workspace-to-document identity reference. It follows
  path changes, survives zero views, refuses a pathless document, and remains
  represented when the resource is unavailable.
- Resource/view tokens carry document revision and view epoch. Results are
  rejected after edit, rename, move, close, branch mismatch, or replacement.
- Pyzo peer editors receive document/view identities and expose the service via
  `pyzo.application.documents`. Parser jobs and results use durable document
  keys and captured tokens; vanilla/legacy parsing retains `editor.id()`.

Persisted workspace documents, immutable per-workspace recovery, conflict
lineages, unload/reload, execution assignment, breakpoint overlays, and tool
affiliation remain later-stage work.

### State and failure coverage

Fifteen `test_document_resources` cases cover shared cross-workspace edits,
independent view state, dirty/undo/redo, no-op and recursive signals, move
epochs, Save As success/cancel/failure/exception/collision, foreground-save
adoption, branch success/rollback/divergence, main-without-view and broken main,
cache invalidation, Run/recovery payload provenance, final global close, pinned
views, and close-registry workspace movement.

Four nested parser tests prove durable job/result keys, stale-token rejection,
retired-view no-fallback, wrong-branch rejection, and unchanged legacy behavior. The existing lifecycle
suite continues to cover multi-document choice collection, failed saves,
cancel, discard, application retention, cleanup failures, and lifecycle-neutral
placement.

The first real replay exposed a delayed Qt `textChanged` emitted after view
retirement. This was the enumerated stale-close state: the adapter now treats
that callback as a no-op, and its controller test asserts the behavior.

### Transitional-reference census

The Stage 2 scan used:

```sh
rg -n '_mainFile|lifecycleId|named_document_id|_peerRecoveryId|parserDone|getCurrentEditor' \
  deps/pyzo/pyzo/core --glob '*.py'
```

- Peer resource identity no longer uses `FileItem.lifecycleId`; that live-only
  compatibility property remains for legacy callers.
- Peer parser requests/results no longer use mutable filename/editor identity.
- `_mainFile` remains the legacy tab-local compatibility projection. The new
  identity-based workspace-main model is authoritative for concurrent-workspace
  implementation; UI command migration follows with the workspace profile and
  persistence stages.
- `_peerRecoveryId` and path-derived recovery helpers remain the existing
  single-workspace persistence compatibility boundary. Stage 3 will migrate
  recovery records and loaded-workspace manifests together rather than encode
  a partial format in Stage 2.
- Ambient `getCurrentEditor()` sites outside parser/resource synchronization
  retain their Stage 4 execution or Stage 6 tool/action classifications from
  the Stage 1 census.

### Verification

- Coordinating suite: **181 passed, 3 expected capability skips**.
- Focused shared document plus lifecycle suite: **54 passed**.
- Nested controller, parser-provenance, Run, shell-command, and shell-group
  direct tests: **9 passed**.
- Touched root and nested Python 3.12 compilation: **passed**.
- Root and nested `git diff --check`: **passed**.
- Legacy QtADS offscreen replay with config saving disabled: foreground
  ordering, independent editor/shell docks, debugger routing, tools, drop
  guides, toolbar enablement, and shutdown **passed**.
- Peer offscreen replay with config saving disabled completed the full editor,
  dirty lifecycle, shell, zero-frame, Run/live-debug, postmortem, multi-kernel,
  and shutdown sequence without the stale-view traceback. A later rerun met
  the previously recorded intermittent status-projector timing assertion; the
  durable parser tests and peer controller/resource smoke passed before it.

### Accepted revision baseline

- Root before Stage 2 commit: `6e8e7c34264ff7dca6e31e7e373b37f16cf2973b`
- Nested Pyzo before Stage 2 commit:
  `c2903fc7467c0ebe24fab13c8235715cf3477b2f`
- Accepted nested Pyzo Stage 2 revision:
  `9762fd5c934dbdb2e3e3c3efd3c54672fe6fa7f8`
- PySide6-QtAds binding used by peer control:
  `764eb4a487abccb162dcbee1a8f0383916561e0e`

The accepted nested Stage 2 revision is recorded before the root evidence
commit. The root revision is the commit containing this section and is reported
in the local handoff and completion response.

## Stage 3 — versioned persistence, recovery, and ordinary lifecycle

Accepted on 2026-07-25.

### Delivered substrate

- `WorkspacePersistenceStore` separates a versioned process manifest,
  independently checksummed workspace records, shared-resource references, and
  independently checksummed workspace recovery records.
- Complete generations publish through record write/fsync, generation rename,
  manifest write, and atomic manifest replacement. The prior manifest remains
  authoritative on every injected failure. One previous complete generation
  and every cross-generation record still referenced by the current manifest
  are retained.
- The process loaded set is distinct from the durable workspace catalog.
  Unloading therefore retains the workspace record needed for reload.
- A corrupt workspace record is isolated as an unavailable, retryable
  workspace. Healthy workspaces remain usable and can publish later generations
  while the manifest carries an opaque reference to the failed record.
- Legacy `peerWorkspaceSession` state migrates into exactly one default
  workspace. Named views remain snapshots rather than loaded identities. The
  complete JSON-compatible legacy config is backed up and retained under an
  explicit application-owned round-trip field, including unknown tool and
  deprecated fields. Migration retry and an already-migrated second invocation
  are idempotent.
- `DocumentResourceRegistry` has a transactional JSON-compatible durable
  snapshot for document/view identities, clean/dirty baseline, undo/redo,
  paths, availability, workspace ownership, view state, pins, and mains.
  Restoration installs no save handlers and performs no file writes.
- `WorkspaceRecoveryRegistry` owns immutable snapshots by
  `(workspace_id, document_id)`. Several workspaces may retain divergent
  versions under one document identity.
- Restore uses content equality: identical retained/external content is clean
  despite changed signatures or timestamps. Genuine divergence retains
  retained and external lineages with timestamps, signatures, content digests,
  capture/save metadata, and workspace-local provenance.
- Conflict resolution clears equivalent conflicts only in currently loaded
  workspaces with the same document, retained version, and observed external
  version. It does not mutate the immutable snapshot. Unloaded workspaces
  retain their snapshot and reassess the current external version on reload.
- `WorkspaceLifecycleCoordinator` transactionally composes stable capture,
  frozen recovery, topology detach, durable loaded-set publication, rollback,
  and reconstruction. It distinguishes unload from final-view close and can
  unload several workspaces as the single transaction used by Quit/Restart.
- Shared-document references identify resources that a detaching workspace
  must not dispose while a surviving workspace still owns a view.

### Peer integration

- Peer startup loads or atomically migrates the versioned store before creating
  the default workspace, so workspace identity survives restart.
- Ordinary peer configuration saves publish the current session and merge only
  the current workspace's document views/main into the shared-resource record;
  records belonging to other loaded or unloaded workspaces are retained.
- Persisted document and view identities are reassociated by durable recovery
  identity or normalized path when editor panes restore. Main designation is
  restored by document identity.
- Compatibility recovery snapshots now carry workspace affinity and prefer the
  durable document identity over the old path-derived identifier.
- Peer recovery conflict detection compares retained text with the external
  text. A metadata-only timestamp/signature change no longer creates a false
  conflict.
- Process/resource corruption blocks destructive publication and is surfaced
  in status and stderr. An individual unavailable workspace is surfaced but
  does not veto persistence by a healthy workspace.
- `PYZO_TEST_WORKSPACE_PERSISTENCE=1` opts the otherwise side-effect-free
  `--test` path into isolated real migration/save/restart verification.
- Legacy QtADS and non-peer paths leave `pyzo.workspacePersistence` unset and
  retain their existing session/config behavior.

### State and failure coverage

The Stage 3 tests directly cover:

1. two-workspace restart round trip with topology payloads, shared documents,
   mains, pins, unknown fields, and independent dirty snapshots;
2. corrupt workspace and recovery isolation, visible unavailable identity,
   repair/retry, and healthy-workspace commits beside a failed peer;
3. record-write, record-fsync, generation-replace, manifest-write, and
   manifest-replace failure with the prior generation remaining authoritative;
4. legacy backup, named-view non-promotion, unknown/deprecated field retention,
   interrupted migration retry, and idempotence;
5. workspace copy with a fresh identity and no mutable aliases;
6. durable document/view/main identity and state round trip with transactional
   invalid-record rejection and no save callback;
7. independent immutable workspace snapshots for one shared document;
8. equality-based clean restore, divergent/missing conflict lineages,
   timestamps and provenance;
9. loaded-equivalent propagation, loaded-nonequivalent isolation, unloaded
   non-propagation, and later reassessment;
10. unload/reload, frozen recovery, shared-resource preservation, stale-capture
    rejection, cancellation, durable-commit rollback, construction rollback,
    and multi-workspace Quit/Restart rollback; and
11. direct external-file byte and mtime invariants across restore, conflict
    resolution, unload, and reload.

### Verification

- Coordinating root suite under Python 3.12/PySide6/QtADS: **210 passed,
  3 expected capability skips**.
- Focused persistence, recovery, lifecycle, and document-resource suite:
  **44 passed**.
- Nested application-controller boundary test: **passed**.
- Touched root and nested Python 3.12 compilation: **passed**.
- Root and nested `git diff --check`: **passed**.
- First isolated peer persistence replay: complete editor, lifecycle, shell,
  Run/live-debug, postmortem, multi-kernel, save, and shutdown sequence
  **passed**; the published generation loaded with one workspace, no issues,
  and one legacy backup.
- Second replay against the same directory restored the same durable workspace
  identity, completed the full replay, published a later generation, and kept
  the legacy backup count at one.
- Final legacy QtADS offscreen replay: foreground ordering, editor/shell docks,
  debugger routing, tools, guides, toolbar enablement, and shutdown **passed**.

### Accepted revision baseline

- Root before Stage 3 commit: `09ca1af129985a51788f7abb335e19afb911420a`
- Nested Pyzo before Stage 3 commit:
  `9762fd5c934dbdb2e3e3c3efd3c54672fe6fa7f8`
- Accepted nested Pyzo Stage 3 revision:
  `031d26e5cfb91028c945af93e2ff67614370c5ba`
- PySide6-QtAds binding used by peer control:
  `764eb4a487abccb162dcbee1a8f0383916561e0e`

The root Stage 3 revision is the commit containing this section and is reported
in the local handoff and completion response.

## Post-stage default-startup correction

Manual review exposed four integration gaps at the migration/factory boundary:
legacy editors and tools leaked into a fresh peer workspace, the initial ADS
topology did not match Pyzo's default arrangement, File Browser opens created
new frames, and Source Structure could reject parser results produced before
durable peer identity assignment.

The correction establishes these rules:

- a fresh or still-pending migration starts with one scratch editor and does
  not activate the legacy editor/session/tool layout;
- the factory topology is one editor above one shell, with Source Structure and
  File Browser to their right;
- a newly opened file joins the most recently active eligible editor group in
  its workspace, retaining its temporary frame only as a safe fallback; and
- parser result matching and lifecycle requeueing use durable document/view
  identity after peer registration.

The coordinating contract now supports composing registered panes that already
occupy temporary frames, and exposes pane-placement state for that integration
boundary.

### Correction verification

- Fresh-start end-to-end peer harness: one scratch editor, exact default tool
  set and topology, same-group File Browser open, and populated Source
  Structure: **passed**.
- Full published-binding Pyzo smoke, including editor grouping, shell/debug
  routing, tool hosting, workspace lifecycle, Run/live-debug, postmortem, and
  multi-kernel behavior: **passed**.
- Coordinating root suite: **211 passed, 3 expected capability skips**.
- Focused root contract/lifecycle suite: **40 passed**.
- Nested parser provenance suite: **5 passed**.
- Legacy QtADS control, Python compilation, and root/nested diff checks:
  **passed**.

The rapid custom-binding status/menu projection artifact remains outside this
correction; ordinary custom-binding startup and the published-binding control
remain functional.

Accepted nested Pyzo correction revision:
`e46e1cf` (`Align peer startup with Pyzo defaults`).

## Stage 4 — execution-routing substrate (in progress)

Started on 2026-08-01. This section records the accepted pure-model slice; it
does not mark Stage 4 complete.

### Delivered substrate

- `ExecutionRouter` registers live workspaces, workspace-owned document views,
  durable live shell identities, and replaceable kernel-generation identities.
- Workspace-implicit routing selects only the currently foregrounded eligible
  shell in the invoking workspace. The model stores no recency fallback queue.
- View-local explicit assignment is sticky across focus and successful kernel
  recycle. Unexpected target loss becomes an explicit broken state until
  reconnect or clear; confirmed closure resets affected views to implicit.
- Cross-workspace explicit assignment is rejected. Moving an assigned view or
  its shell makes the assignment broken instead of silently retargeting it.
- Shell movement changes view ownership immediately while retaining distinct
  process-workspace provenance. Failed recycle leaves that transitional state;
  successful recycle installs a new generation and completes migration.
- Every resolution returns immutable workspace, view epoch, shell, shell
  epoch, kernel-generation, process-workspace, command, policy, and operation
  provenance. Validation rejects delayed results after routing-relevant state
  changes while keeping direct shell operations stable across unrelated focus.
- Execute Selection, Line, Cell, File, and Main share buffer/no-save policy.
  Run File/Main as Script share autosave/recycle policy. Completion, help, tool,
  and debugger requests use the same provenance carrier.

### State and failure coverage

The focused truth table covers two-workspace isolation, lack of recency
fallback, sticky explicit assignment, unexpected loss, reconnect, clear,
confirmed close, cross-workspace rejection, view movement, shell movement,
repeated movement, failed and successful recycle, implicit and direct stale
response validation, and all initial Execute/Run-as-Script command policies.

### Verification

- Focused execution-routing suite: **9 passed**.
- Complete non-Qt coordinating suite: **174 passed**.
- Python 3.12 compilation and root `git diff --check`: **passed**.
- The all-module discovery run reached the same 174 passing tests; three Qt
  modules could not import because the lightweight verification environment
  does not contain PySide6. No Qt-owned source changed in this slice.

### Remaining before Stage 4 acceptance

Live Pyzo integration must register real document views, shells, foreground
events, kernel generations, and closure/recycle outcomes; route every Execute
and Run-as-Script command through the resolver; project assignment and
transitional state; reject asynchronous results at consumers; and replay the
real-kernel, peer, and legacy acceptance workflows.

### 2026-09-06 lifecycle-projector correction

The status and command projectors now reconcile against the QtADS manager's
authoritative live floating-window set. This removes still-valid retired
windows after editor close/replacement, before deferred Qt destruction has
invalidated the old widget. A focused regression covers that state; the status
and command projector suites pass 18/18, and the execution-routing proof
passes 9/9.

The relocated `deps/pyzo/.venv` was rebuilt with Python 3.12,
PySide6/shiboken6 6.11.1, IPython, and the prebuilt local PySide6-QtAds wheel.
The offscreen Qt projector suites pass in that fresh environment. The complete
peer smoke then passed the clean/dirty editor lifecycle, ordinary run/live
debug, post-mortem re-entry, and multi-kernel execution-affinity checks after
the projector correction.
