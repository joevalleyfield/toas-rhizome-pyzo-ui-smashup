# Local workspace scope — 2026-09-06

## Decision and precedence

Prioritize reliable local workspaces and durable editing state. Establish the
ordinary workflow before portability, synchronization, or preservation of live
processes across workspace closure. This records the user's decisions and the
scope judgments delegated during the 2026-09-06 requirements discussion.

This amendment is normative where it conflicts with the July concurrent-
workspace baseline, application topology, or Experiment 014. Previous acceptance
evidence remains a record of the earlier contract, not proof of this amendment.
No runtime changes or new acceptance results are implied by this document.

## Initial product contract

### Workspaces and folders

- Several named workspaces may be open in one application. Each frame belongs
  to one workspace; a workspace may span several peer frames.
- A workspace retains its layout, view state, contextual preferences, tool
  state, command history, and document references. It usually has a folder
  root, but a root is optional. Sibling and nested roots are valid.
- Folder containment does not own documents, force workspace membership, or
  create a parent/child workspace lifecycle. External files may be opened.
- The application remembers known workspaces and which are open. Normal
  restart reopens that open set. Explicitly closed workspaces stay closed until
  requested; a failed restore remains visible and retryable.

### Shared documents and file operations

- Views of the same file share one document identity, current text, dirty
  baseline, and undo/redo state. Cursor, selection, scroll, and placement belong
  to each view. A workspace boundary does not create a content fork.
- Moving a buffer view to another workspace preserves its document, unsaved
  edits, and disk path. It carries its view state. Execution assignment cannot
  silently point into the previous workspace after transfer.
- Moving or renaming a file preserves its document identity; all references
  follow the new path. Disk relocation is explicit and shows the destination.
  Folder topology may suggest a destination but never triggers an implicit move.
- Fork to New File creates a distinct document at a separately chosen path,
  initialized from current buffer contents, including unsaved edits. On success
  the initiating view follows the fork; other views keep the original. Failure
  or cancellation leaves the original and its views intact. Existing destination
  files must not be silently overwritten.
- Rename/Move and Fork are distinct operations. The old Save As wording must
  not be used to infer whether other views disconnect.

### Retention and close/reopen

- The application durably retains document editing state independently of open
  views and workspaces, including named and untitled buffers and undo/redo
  history. Workspaces durably retain their view state and document references.
- Closing a tab, its final view, a workspace, or the application does not
  discard edits or require saving to the source file. A closed buffer remains
  discoverable and reopenable through a retained/closed-buffer list. Closing a
  tab does not make it automatically reappear on restart.
- Closing a workspace remembers its open-view arrangement and suspends its
  participation in shared documents. Reopening restores that arrangement using
  the latest retained document state. Old view positions are adjusted safely
  when the shared text has changed.
- Example: close A while B shares its unsaved document; edit in B; restart with
  only B open; reopen A. Both views show the latest retained edits. Closing B
  too does not lose the document or require reopening B to retrieve it.
- Closed workspaces do not own frozen, competing versions of shared document
  contents. Historical checkpoints may aid recovery, but are not silently
  restored as a workspace's private live version.
- Save explicitly updates the user's file and its clean baseline. Save does
  not authorize forgetting undo/view state. Discard explicitly abandons retained
  edits; its shared-document effect must be clear to the user. Forgetting a
  retained buffer is also explicit. Closure and workspace removal are not
  implicit garbage-collection authority for editing state.
- Retention is automatic during editing, not only on orderly shutdown. An
  orderly close must make the affected state durable or remain open with a
  visible failure and recovery options. Runtime failure must not falsely report
  that the state was retained.
- Crash recovery must have a documented, tested maximum persistence interval;
  edits made after the last durable write may be lost on a crash. Choose the interval
  during the retention proof using measured behavior. Store format, compaction,
  and history representation are engineering choices, not user design chores.
- If disk content changes externally, retain both the working state and the
  observed external version for explicit reconciliation. Reopening must not
  overwrite either silently. Conflict state is document-owned, so its resolution
  is shared; closing a workspace alone does not create a conflict.

### Execution and safe closure

- Keep workspace-local implicit execution and view-local explicit assignment,
  with visible missing/broken targets, no cross-workspace fallback, and rejection
  of stale asynchronous results. Preserve existing Execute versus Run-as-Script
  save/recycle behavior; user-invoked Run-as-Script remains an explicit operation.
- Shells stay in their owning workspace for the initial release. Rearrangement
  within that workspace is supported; cross-workspace shell transfer is refused
  visibly. Users may create another shell in the destination workspace.
- Closing a workspace with live shells offers terminate-and-close or cancel.
  Debug/postmortem warnings identify loss of live interpreter/stack state. A
  cancelled close keeps the workspace intact. Retention failure must be resolved
  before irreversible shell termination or view teardown.
- Ordinary Run, live debugging, postmortem inspection/execution, and independent
  kernel targeting remain requirements. Surviving a workspace close with a live
  debugger is deferred. No zombie workspace is created in the initial model.
- Preserve the remaining workspace-local breakpoint and tool isolation rules;
  defer migration-specific overlays and zombie reconciliation. Global UI settings
  such as theme/language may use the existing explicit application-wide fallback.

## Deferred until after the local workflow

- Portable export/import, cross-machine synchronization, concurrent distributed
  editing, and restoring another machine's environments or live processes.
- Live-shell migration, transitional process/workspace ownership, detachable
  kernels, multiple views over one kernel, zombie workspaces, and their reopening
  or breakpoint reconciliation machinery.
- Frozen per-workspace document recovery branches, generalized historical
  workspace rollback, and automatic disk relocation during view transfers.
- Fully independent workspace themes/languages, richer tool bindings, and broad
  Rhizome/TOAS integration. These do not block the local workspace proof.

Stable identities and explicit paths preserve future options. They do not imply
that portable snapshots or synchronization must be designed or implemented now.
Native platform validation and compatibility obligations remain; this amendment
does not waive them or claim production readiness.

## Consequences for the roadmap

1. Before continuing Stage 4, revise the Stage 2–3 lifecycle/retention acceptance
   contract and assess migration from existing workspace-owned snapshots. Preserve
   divergent old snapshots as recoverable versions; never select a winner or
   delete one merely because the new model expects one shared document state.
2. Prove retention and resume on real editors: last-view closure, untitled
   buffers, undo/redo, A/B shared edits while A is closed, all-workspaces-closed
   retention, restart, external changes, and persistence failure. The retention
   implementation must cover view/undo state as well as text recovery.
3. Resume Stage 4 with real workspace routing and target lifecycle. Its first
   slice may use two workspaces and Execute Selection. Shell migration is no
   longer an acceptance requirement; visible refusal is required instead.
4. Stage 5 retains ordinary debugger/breakpoint isolation and conservative
   workspace closure; zombie and shell-migration requirements are deferred.
   Stages 6–7 retain contextual tools/settings and integrated compatibility work.

The old seven-stage descriptions and risk ratings require a targeted scope
reconciliation before implementation. Accepted foundations and historical tests
are preserved; changed requirements receive new evidence rather than retroactive
claims of completion.
