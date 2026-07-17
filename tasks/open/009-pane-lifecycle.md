# Experiment 009: Separate pane, frame, and application lifecycle

## Status

In progress. Every lifecycle matrix, including backend hide/destruction
enforcement, is implemented and verified. The final slice awaits an accepted
commit before the execution checklist advances to Experiment 004.

## Objective

Prove that document and interpreter lifecycle remains correct when panes and
peer frames are closed, moved, or restored through the docking backend.

## Dependencies

- Experiment 006 defines close negotiation and state transitions.
- Experiment 007 provides the backend behavior under frame closure.
- Experiment 008 may supply real Pyzo panes; a model pane may be used first.

## Acceptance criteria

- Closing a non-final editor view leaves its document alive.
- Closing the final dirty editor view supports save, discard, and cancel.
- Closing a frame containing multiple dirty documents is transactional: a veto
  or cancellation does not leave an accidental partial close.
- A dead shell can close directly.
- A running shell refuses closure or requires explicit confirmation; moving or
  regrouping it never implies interpreter termination.
- Closing the first-created frame behaves like closing any other frame and does
  not inherently quit the application.
- Empty-frame behavior and application-shutdown policy are explicit and tested
  separately.
- Backend widget hiding or destruction cannot bypass application lifecycle
  policy.

## Allowed write surface

- Peer-frame contract and lifecycle implementation/tests.
- The local Pyzo project surface needed for document and shell policy.
- Root-level experiment notes and this task artifact.

## Completion evidence

Record a state matrix covering clean/dirty documents, final/non-final views,
dead/running shells, single/multiple panes, and frame/application closure.
Include automated results and any backend event paths that required interception.

## Progress evidence

### Explicit application Quit and Restart

Peer-mode application exit no longer closes the hidden `QMainWindow`. An
application-owned shutdown coordinator distinguishes Quit from Restart, enters
one `CloseReason.APPLICATION` workspace transaction regardless of visible-frame
count, and treats resource negotiation as the only cancellable phase. Dirty
documents and live/debugging shells therefore preserve the complete topology
when any choice vetoes exit.

After topology commit, every pane callback and every ordered application
cleanup is attempted once. Committed pane failures are collected rather than
stopping later callbacks. Config, history, command server, residual kernels,
tools, stoppable threads, status projections, and the QtADS backend then clean
up in order. Quit exits 1 if any post-commit cleanup failed; Restart logs such
failures and still attempts process replacement. Replacement failure is fatal
and exits 1. Reentrant or conflicting requests coalesce behind the first
accepted disposition.

The projected peer menus now expose both Restart and Quit. Menu, command-line,
test-harness, native hidden-host close, and non-independent-platform final-frame
paths converge on the application command. Legacy mode retains its existing
`closeEvent()` and Restart implementation as a control.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 121 peer-frame tests passed with three intentional capability skips;
- the real peer-mode smoke passed the complete editor/debugger/movement/dirty/
  shell/zero-frame matrix and exited through the new application transaction;
- an intentionally restricted smoke proved cleanup failures are aggregated,
  later cleanup continues, and Quit exits nonzero;
- the legacy Pyzo control remained green;
- Python compilation and root/Pyzo `git diff --check` passed.

### Clean editor and shared-document views

The close-policy contract now receives an immutable `CloseRequest` containing
the complete pane set and reason for the transaction. A policy can therefore
distinguish closing one of several views from closing every view in a group or
frame; it does not infer finality independently for each pane.

`DocumentViewRegistry` owns document-to-view membership independently from
workspace placement. Its close policy proves these states:

- closing a non-final view removes only that pane and leaves the document alive;
- closing the final clean view closes the document exactly once without setting
  application shutdown;
- a transaction closing all views closes once, while a transaction closing a
  subset preserves the document;
- dirty final-view and pinned-view closure are refused until their explicit
  negotiation slices are installed;
- tabbing and floating do not invoke lifecycle callbacks;
- stale duplicate closure and failed binding rollback are idempotent.

Real Pyzo peer editors now route ordinary `closeFile()` through workspace close
negotiation. The committed document callback uses a separate internal removal
path, so removing the editor host cannot recursively request closure after the
workspace has already committed. Peer mode permits the final editor group to
disappear; opening a new file recreates a document pane without treating the
operation as application Quit.

Stored Pyzo editor state still uses the legacy nested-tab representation. Its
conversion is now an explicit startup migration phase: lifecycle binding is
suspended only around `restoreEditorState()`, the manager distributes restored
items into independent hosts, and completion requires every settled peer host
to contain at most one document before bindings are reconciled. Normal runtime
binding retains the strict one-document-per-editor-pane invariant. Each
`FileItem` carries an immutable lifecycle serial so document identity survives
Qt tab-data wrapper conversion and Save As naming changes.

The real-Pyzo smoke closes one of two clean editors, closes the final editor,
asserts that shell panes and application lifetime remain intact, creates a new
editor, and verifies command/status projection IDs converge with live frame
IDs after deferred deletion.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 73 peer-frame tests passed with three intentional capability skips;
- the real peer-mode Pyzo smoke passed clean editor lifecycle, pane movement,
  debugger routing, native overlays, independent shells, and clean shutdown
  without uncaught exceptions;
- the legacy Pyzo layout control remained green;
- Python compilation and root/Pyzo `git diff --check` passed.

### Zero visible frames and default-frame recreation

`ApplicationFrameLifecycle` now owns the policy above workspace topology. It
asks whether the platform retains a usable application-level handle after all
windows close. Capable platforms remain alive at zero frames; conventional
window/task-switcher platforms request application Quit. Qt's implicit
last-window shutdown is disabled in peer mode so this decision always passes
through application policy rather than window-system timing.

The deterministic matrix proves:

- zero frames survive only when an independent application handle exists;
- an existing frame makes activation and zero-frame callbacks no-ops;
- activation with zero frames creates one configured default frame;
- unreadable or raised configured-template failures are logged and fall back
  once to the factory template;
- a configured template that constructs no pane also falls back;
- failure of the factory template, or completion with no pane, reports detail
  and requests exit status 1;
- reentrant activation bursts coalesce into one bounded pending indication and
  cannot accumulate frame-creation work.

Pyzo's macOS peer path binds application activation to this controller. Its
current configured template uses remembered tool IDs, falling back to source
structure and file browser, and composes editor, shell, and tool panes into one
ordinary peer frame. Individual editor, shell, and tool construction failures
are logged independently so successful panes remain usable. Tool panes now
have committed lifecycle cleanup, preventing a zero-frame transition from
leaving stale tool-manager registrations.

The real macOS smoke merges all surviving resources into the final frame,
closes it natively with document/shell policy, proves that workspace and all
resource registries reach zero without application shutdown, then simulates
activation. Exactly one peer frame is recreated with editor, shell, and tool
pane kinds. Explicit New/Open composition with this same default-frame request
belongs to the upcoming application-command lifecycle slice.

Zero-frame survival and activation recreation are fixed platform policy for
this prototype. User-configurable preferences are recorded as follow-on work;
they may never create an unreachable tray/hidden-window process where no
independent handle exists.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 110 peer-frame tests passed with three intentional capability skips;
- the real peer-mode zero-frame survival and default-layout recreation smoke
  passed;
- the legacy Pyzo control remained green;
- Python compilation and root/Pyzo `git diff --check` passed.

### Native peer-frame closure and creation-order symmetry

Before this slice, calling the native close affordance on a populated QtADS
floating container hid the window while leaving its application frame and panes
registered. No close policy ran. `QtAdsPeerFrameBackend` now installs a bounded
frame-close filter: a populated peer frame delegates to an application-supplied
close request, while an empty source wrapper produced during drag/merge remains
structural QtADS cleanup.

The deterministic backend matrix proves:

- first-created, later-created, and final visible populated frames each invoke
  exactly one `CloseReason.FRAME` prepare, validate, and committed callback;
- accepted closure removes only the requested frame, whether Qt deletes its
  wrapper immediately or leaves it hidden;
- cancellation preserves the complete topology and keeps the native window
  visible;
- closing the final visible frame does not set `shutdown_requested`;
- empty source-wrapper destruction during a direct QtADS merge emits no
  application frame-close request;
- stale/deleted wrappers cannot be mistaken for another live frame;
- backend rendering and explicit backend teardown do not re-enter the native
  user-close bridge.

Pyzo binds the bridge to one composite application resolver. Live-shell choices
are gathered before dirty-document saves; if a wider document transaction
cancels, provisional shell termination approval is revoked. A real mixed-frame
smoke places two dirty documents and one live shell together, approves shell
termination, cancels one document, and proves that all panes, dirty markers,
the interpreter context, and topology survive. A separate disposable native
frame proves accepted title-bar closure without application shutdown. Legacy
mode remains outside the peer-only bridge.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 103 peer-frame tests passed with three intentional capability skips;
- the real peer-mode native accepted/cancelled/mixed frame-close smoke passed;
- the legacy Pyzo control remained green;
- Python compilation and root/Pyzo `git diff --check` passed.

### Transactional dirty-document negotiation

Dirty-document closure now separates negotiation, validation, and commit. The
workspace first gathers one save/discard/cancel choice for each affected
document, performs no saves if any document cancels, attempts all requested
saves before changing topology, and revalidates document state immediately
before commit. Discard is deferred until the committed final-view callback.

The model matrix proves:

- a dirty document with a surviving view closes the departing view without a
  prompt;
- all closing views of one dirty document produce one document-level prompt;
- Save, Discard, and Cancel have distinct dispositions;
- Cancel, a raised save error, a false save result, or a document that remains
  dirty vetoes the complete topology transaction;
- choices for multiple documents are collected before any save side effect;
- a later save failure cannot roll back an earlier filesystem write, but no
  pane topology is committed;
- pinned, stale, generic-confirmation, and reentrant-close paths cannot bypass
  validation.

Real Pyzo peer editors expose a side-effect-free dirty-close chooser while the
existing legacy close path retains its behavior. The peer smoke covers Save As
cancel/failure, explicit cancel, discard, an actual file save, and a two-dirty-
document frame transaction. It also guards editor lifecycle rebinding while a
committed departing host is being destroyed.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 82 peer-frame tests passed with three intentional capability skips;
- the real peer-mode Pyzo dirty-editor matrix and clean shutdown passed without
  uncaught exceptions;
- the untouched legacy Pyzo control remained green;
- Python compilation and root/Pyzo `git diff --check` passed.

### Retained dirty buffers

Application Quit and Restart now resolve dirty documents through an automatic
`RETAINED` disposition. Ordinary pane, group, and frame closure still expose
only Save, Discard, and Cancel. Pinned views retain their ordinary close
protection but, matching legacy application shutdown, do not veto application
exit after dirty content is durable.

`RecoveryStore` writes versioned document records into complete generations
and atomically replaces one manifest. Record files and generation directories
are synchronized before the manifest becomes authoritative. A failed content
or manifest write leaves the previous generation usable. Multiple documents
commit one at a time, so a successful earlier snapshot remains reusable if a
later document fails. Retry targets only unresolved documents.

Snapshots include stable named or untitled identity, text, encoding, BOM
behavior, preferred line endings, the named file's disk signature, and an
optional workspace-affinity field. Unchanged snapshots cause no write. Save
and committed Discard retire a snapshot; an explicitly approved discard can
invalidate a stale record without requiring new disk allocation.

Startup restores valid records after ordinary editor-state migration and
before command-line file opens. Existing named editors are merged rather than
duplicated; missing or externally changed files restore as dirty conflicted
buffers while disk bytes remain untouched. The editor title receives a warning
marker and application status explains the conflict. Invalid schemas,
digests, metadata, duplicate identities/paths, and partial records are
quarantined independently so valid documents still restore.

Snapshot failure is pre-commit and offers Retry, Save affected, Discard
affected and exit, or Cancel. Save failure and Cancel preserve topology and
prevent cleanup, Quit, or Restart. Automatic retention is fixed on for this
prototype; preference UI, exact prior layout placement, and continuous crash-
time backup remain follow-on work.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 141 peer-frame tests passed with three intentional capability skips;
- a real named-file smoke restored dirty text, CRLF/BOM metadata, and a visible
  external-file conflict without changing the replacement disk content;
- an actual application Quit automatically retained one dirty untitled buffer,
  and an independent process verified its durable record and stable identity;
- the full peer editor/debugger/movement/shell/zero-frame smoke and legacy Pyzo
  control remained green;
- Python compilation and root/Pyzo `git diff --check` passed.

### Dead and live shell closure

`ShellLifecycleRegistry` now owns shell identity and termination approval
independently from frame placement. Its policy classifies dead, idle, running,
debugging, and starting/unknown states. Dead shells close directly. Every live
state requires an explicit terminate-and-close choice while detachable kernels
remain unavailable; cancellation leaves both interpreter and topology intact.

The model matrix proves:

- idle, running, debugging, and starting/unknown shells all require explicit
  termination approval;
- frame closure gathers every affected shell choice before committing and a
  cancellation closes no shell;
- live-state transitions remain covered by the explicit termination choice;
- a dead shell that becomes live before validation is refused rather than
  closed under stale authority;
- a confirmed live shell that dies before commit closes without a redundant
  termination request;
- generic confirmation and reentrant negotiation cannot bypass shell policy;
- tabbing and floating invoke no shell lifecycle callback.

Real Pyzo maps broker connectivity, interpreter state, and debug mode into this
application state model. Direct `closeShell()` and model-driven pane closure use
the same peer policy, while a committed internal path performs cleanup exactly
once after topology changes. The user warning distinguishes idle, executing,
debugging, and uncertain interpreters; debugging explicitly warns that captured
stack state will be lost. The legacy layout retains its original direct close
path.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 94 peer-frame tests passed with three intentional capability skips;
- the real peer-mode smoke cancelled one live-shell close, preserved it, then
  approved termination and removed it exactly once;
- real-pane movement preserved the shell context and debugger-facing widgets;
- the legacy Pyzo control passed its original shell-close workflow;
- Python compilation and root/Pyzo `git diff --check` passed.

Interpreter termination is asynchronous and occurs after topology commit. A
later termination failure cannot roll topology back; surfacing and recovering
post-commit cleanup failures remains part of the queued frame/application
lifecycle work.

### Placement-only lifecycle invariants

A counting-policy harness now wraps real document-view and shell policies while
exercising every application placement path. It combines a dirty shared
document (including a pinned view) with dead, idle, running, debugging, and
starting/unknown shells. After every operation it asserts identical pane and
policy identity, unchanged document membership and dirty state, unchanged shell
registry/state, zero saves/closes/termination dispositions, zero close-policy
phase calls, and no application shutdown request.

The matrix covers:

- same-group activation and same-frame/cross-frame tab regrouping;
- float with a surviving source frame and float that empties its source frame;
- inner and outer splits in all four directions, both cross-frame and from a
  shared group;
- valid settled backend-layout adoption without model republishing;
- invalid membership-changing and duplicate backend layouts;
- unknown, self-targeting, conflicting-frame-ID, and unsupported operations;
- backend render failure after a synchronous placement mutation.

The final render-failure case establishes the lifecycle boundary only: no
resource lifecycle callback runs. Placement rollback/reconciliation after an
arbitrary backend render exception is a separate adapter-atomicity concern and
is not silently treated as document or interpreter closure.

The real Pyzo movement smoke now additionally proves that the editor's Qt
document object and dirty marker, document-view registration, shell lifecycle
registration, shell context, shell host, debugger controls, and dock objects
retain identity across tab, inner split, outer split, float, and cross-frame
movement. Deferred frame-wrapper deletion does not disturb those identities.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 99 peer-frame tests passed with three intentional capability skips;
- the real peer-mode Pyzo movement and lifecycle smoke passed;
- the legacy Pyzo control remained green;
- Python compilation and root/Pyzo `git diff --check` passed.

### Backend hide and destruction enforcement

QtADS pane close affordances now use `CustomCloseHandling` and enter one
application-owned pane transaction. Pyzo supplies its composite document/shell
resolver, so dirty-editor and live-shell choices remain identical whether the
request originates in Pyzo or native dock chrome. Cancellation leaves both the
model and visible projection intact.

One projection-lifecycle filter now distinguishes supported user closure from
backend drift and authorized teardown:

- a populated peer-frame close enters the existing transactional frame path;
- a native pane close enters `request_close_pane` exactly once;
- forced logical close and raw active-pane or populated-frame hide are rejected
  as projection drift and repaired from authoritative application state;
- hiding an inactive tab during ordinary tab selection remains valid and is
  never "repaired" into the foreground;
- deferred deletion of a live pane or populated frame is rejected before Qt
  can destroy application-owned content;
- empty drag-source wrappers, accepted model removal, and whole-backend
  teardown retain their structural hide/delete behavior;
- irreversible immediate destruction cannot mutate application topology or
  masquerade as closure. It removes the stale wrapper from backend tracking and
  records a terminal backend invariant error instead of fabricating replacement
  editor or shell content.

The deterministic matrix covers an allowed pane within a multi-tab group,
cancelled pane closure, forced close, raw dock/frame hide, normal inactive-tab
hide, deferred pane/frame deletion, and immediate out-of-band pane destruction.
Existing command and status destruction tests now first close their frames
through application policy and then verify projection cleanup.

Verification on macOS with Pyzo 4.21.0 and CPython 3.12.13:

- all 147 peer-frame tests passed with three intentional capability skips;
- the real peer-mode smoke passed editor/debugger routing, placement, clean and
  dirty document lifecycle, independent shell lifecycle, zero-frame default
  recreation, and application shutdown;
- the legacy Pyzo control passed its original ADS, editor, debugger, and shell
  workflow;
- Python compilation and root/Pyzo `git diff --check` passed.
