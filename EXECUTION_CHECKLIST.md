# Execution Checklist

This is the mutable execution order for the feasibility spike. Experiment
numbers remain stable evidence and acceptance references; they are not the
current work queue. Follow this checklist from top to bottom and keep exactly
one item marked **NEXT**.

## How to use this checklist

- Finish or explicitly defer every sub-item before advancing to the next
  numbered section.
- Link every deferral to the later experiment that owns it; do not silently
  drop an acceptance criterion.
- If a discovery blocks the current acceptance criterion, insert it directly
  beneath that criterion.
- If a discovery belongs to an adjacent or later experiment, record it there
  and resume the current item.
- Do not turn an architectural observation into a wholesale rewrite unless the
  current experiment requires that rewrite to satisfy a tested invariant.
- Commit an accepted implementation slice before moving the **NEXT** marker.

## 0. Locked prerequisites

- [x] [Experiment 001 — Pyzo baseline](tasks/closed/001-baseline-pyzo.md)
- [x] [Experiment 002 — independent docking spike](tasks/closed/002-docking-spike.md)
- [x] [Experiment 006 — technology-neutral peer-frame contract](tasks/open/006-peer-frame-contract.md)
- [x] [Experiment 007 — QtADS peer-frame adapter](tasks/open/007-qtads-peer-frame-adapter.md)
- [x] Reconcile [Experiment 003 — Pyzo editor groups](tasks/open/003-pyzo-editor-groups.md)
  after the current tab-edge slice. Its reusable editor/shell evidence has
  already fed Experiment 008, but its remaining product-level bullets must be
  closed, transferred, or explicitly superseded before its status changes.

## 1. Finish the macOS interaction slice of Experiment 011

Reference: [Experiment 011 — per-group tab edges](tasks/open/011-per-group-tab-edges.md).

- [x] Store top, bottom, left, and right on application-owned group state.
- [x] Render independent four-side groups through the bounded QtADS/binding
  fork and preserve mixed-side layout state.
- [x] Expose a checked, group-local `Tab position` command in Pyzo peer mode.
- [x] Preserve individual-tab reorder/undock behavior and add whole-group drag
  and context-menu behavior to empty bottom/left/right rail space.
- [x] Record the macOS rail interaction acceptance and exact fork revisions.
- [x] Decide rail-local list-all-tabs policy.
  - [x] Keep the existing top horizontal affordance.
  - [x] Give bottom horizontal rails an equivalent colocated dropdown.
  - [x] Defer a left/right affordance. Re-evaluate it in Experiment 010's
    portability/UX matrix after Experiment 008 establishes the application-menu
    projection; do not infer vertical policy from current QtADS placement.
- [x] Implement and test the bottom rail list-all-tabs dropdown.
  - [x] Colocate the dropdown with the bottom tab rail rather than leaving it in
    the top title-bar composition.
  - [x] Preserve the existing tab list, active-tab selection, configuration
    flags, and dynamic visibility/overflow behavior.
  - [x] Move the affordance back to the top composition when a group returns to
    top tabs; never show duplicate controls.
  - [x] Preserve bottom gutter group drag/context behavior and individual-tab
    behavior.
  - [x] Cover direct switching and mixed-side layout restoration.
  - [x] Keep a one-pane non-top rail visible so the pane and group remain
    draggable when packed beside another group.
- [x] Record accessibility, keyboard focus, high-DPI, and minimum-size results,
  or link each unrun obligation to Experiment 010's portability matrix.
  - [x] Expose stable accessible names for tabs, renamed tabs, per-tab close
    buttons, and the list-all-tabs button on every edge.
  - [x] Verify that side changes preserve pane-content focus and do not admit
    the custom QtADS chrome into the ordinary focus chain.
  - [x] Verify the direct suite and a rendered layout at 100%, 125%, and 200%
    scale factors.
  - [x] Verify orientation-aware minimum-size hints and unclipped hard-minimum
    content for all four sides.
  - [x] Transfer direct keyboard tab traversal and non-macOS accessibility,
    scaling, and platform-style replay to Experiment 010.
- [x] Update Experiment 011 status to distinguish accepted macOS behavior from
  deferred Windows/Linux evidence.

## 2. Reconcile Experiment 003 before deeper Pyzo changes

Reference: [Experiment 003 reconciliation and conclusion](tasks/open/003-pyzo-editor-groups.md#reconciliation-and-conclusion).

- [x] Map every remaining Experiment 003 criterion to evidence already supplied
  by Experiment 008 or to a concrete remaining gap.
- [x] Do not implement legacy arbitrary-target/group commands if the peer-frame
  command model supersedes them.
- [x] Record which editor-group work is superseded by document-level peer panes.
- [x] Close Experiment 003 or leave it open with only genuinely unmet criteria.

## 3. Complete Experiment 008 application chrome and command ownership

Reference: [Experiment 008 acceptance criteria](tasks/open/008-pyzo-pane-projection.md#acceptance-criteria)
and [remaining slice](tasks/open/008-pyzo-pane-projection.md#remaining-slice).

- [x] Define application-owned command descriptors and active-context
  resolution without assigning command ownership to `QMainWindow`, a frame, or
  QtADS.
- [x] Register application Quit first and project it into every existing and
  future peer frame while preserving `pyzo.main.close()` confirmation behavior.
- [x] Keep Close Pane, Close Group, Close Frame, and Quit as distinct commands.
- [x] Define menu projection by platform:
  - [x] macOS: one native application menu whose availability does not depend on
    a hidden or surviving privileged window.
  - [x] Windows/Linux: an equivalent menubar projection in every workspace peer
    frame unless platform testing establishes a less surprising convention.
- [x] Synchronize command enablement, checked state, labels, shortcuts, and
  dynamic menus while resolving invocation against the active peer context.
- [x] Project status and focus sufficiently for editor, shell, file-browser,
  and run/debug operation from every peer.
- [x] Inventory every remaining hidden-`QMainWindow` dependency. Treat the host
  as migration scaffolding here; defer wholesale removal unless an acceptance
  assertion requires it.
- [x] Replay the real-Pyzo pane matrix and update Experiment 008 evidence.

## 4. Execute Experiment 009 lifecycle matrices

Reference: [Experiment 009 acceptance criteria](tasks/open/009-pane-lifecycle.md#acceptance-criteria).

- [x] Clean editor: final and non-final view closure.
- [x] Dirty editor: save, discard, and cancel for pane and multi-pane frame
  closure, with transactional veto behavior.
- [x] Shell: dead, idle, running, and debugging closure policy.
- [x] Verify moving or regrouping never closes a document or terminates an
  interpreter.
- [x] Verify first-created, later-created, and final visible frames use the same
  close path.
- [x] Specify zero-visible-frame behavior without equating it to Quit.
- [x] Verify application Quit and Restart independently from frame closure,
  including cleanup failure behavior.
- [x] Specify and prototype retained-dirty application exit/session recovery
  for named and untitled buffers. Keep this explicit session disposition
  separate from ordinary pane/frame Save, Discard, and Cancel negotiation.
- [x] Prove backend hide/destruction cannot bypass lifecycle negotiation.

## 5. Run the non-negotiable debugger acceptance workflow

Reference: [Experiment 004 — core tools and post-mortem debugging](tasks/open/004-core-tools-and-debugger.md).

- [x] Verify ordinary run and live debugging with peer frames.
- [x] Cause an unhandled exception and re-enter its captured post-mortem session.
- [x] Select stack frames and navigate source without a privileged frame.
- [x] Execute live interpreter code against the selected captured frame.
- [x] Repeat after split, float, cross-frame move, re-dock, and relevant frame
  closure.
- [x] Verify breakpoints, traceback navigation, shell state, and debugger
  context survive the complete workflow.

Do not begin toas or rhizome UI integration before this section passes or
produces a clearly bounded blocker.

## 6. Bound forks and portability obligations

Reference: [Experiment 010 — fork boundary](tasks/open/010-fork-boundary.md).

- [x] Attribute every deviation to application policy, peer adapter, Pyzo,
  PySide6-QtAds binding, or QtADS source.
- [x] Decide whether hidden `QMainWindow` removal is required, optional cleanup,
  or blocked by a specific Pyzo service assumption.
- [x] Record exact maintained fork revisions and likely upstreamable slices.
- [x] Run or explicitly schedule Windows and Linux tests for docking, menus,
  shortcuts, focus, high-DPI, and lifecycle.
- [x] Confirm macOS-first choices did not require amputating Windows/Linux
  support.

## 7. Make the integrated feasibility decision

Reference: [Experiment 005 — feasibility decision](tasks/open/005-feasibility-decision.md).

- [x] Replay the full editor, shell, file-browser, run/debug, post-mortem,
  lifecycle, layout, and command/menu acceptance workflow.
- [x] Classify the stack as viable unchanged, viable with bounded maintained
  forks, or unsuitable for the peer-frame application model.
- [x] Record the recommendation and prerequisites for any subsequent
  toas/rhizome transcript-editor integration.

## 8. Remove the hidden Pyzo main window

Reference: [Experiment 012 — hidden-main removal](tasks/open/012-hidden-main-removal.md).

- [x] Introduce the peer application controller and explicit non-window
  compatibility boundary.
- [x] Move editor-context and Run/Debug execution behavior out of the hidden
  menu graph.
- [x] Project the remaining application menus into peer chrome without using
  the hidden menu bar as their behavior owner.
- [x] Replace peer-mode main-window state and named views with
  workspace/session persistence.
- [x] Move dialogs, tool construction, metadata, appearance, and restart to
  application services and active-peer projection.
- [x] Cut peer startup over to the application controller and prove no
  `QMainWindow` exists while the full acceptance replay and legacy control pass.

## 9. Audit state ownership for concurrent workspaces

Reference: [Experiment 013 — workspace state ownership audit](tasks/open/013-workspace-state-ownership-audit.md).

- [x] Inventory every persisted and live Pyzo state/configuration entry point
  using the Experiment 013 matrix schema, without implementing migrations or
  assigning priority.
- [x] Probe consequential scope/lifecycle ambiguities that source inspection and
  existing evidence cannot resolve.
- [x] Complete the source census and record explicit unresolved findings or
  no-meaningful-effect rationales.
- [x] Accept the descriptive audit before beginning follow-up risk analysis or
  multi-workspace implementation.

## 10. Implement concurrent workspaces through explicit risk gates

Reference: [Experiment 014 — concurrent workspace implementation](tasks/open/014-concurrent-workspace-implementation.md),
[requirements baseline](docs/concurrent-workspace-requirements.md), and
[risk analysis](docs/concurrent-workspace-risk-analysis.md).

- [x] Stage 1: establish durable identity lifetimes, multiple workspace
  topology roots, pane ownership, and captured operation context.
- [x] Stage 2: prove shared document content with workspace-owned editor views,
  durable rename/Save As/branch behavior, final-view lifecycle, and closed main
  designation.
- [x] Stage 3: introduce versioned process/workspace persistence,
  partial-failure restore, immutable workspace recovery, conflicts, and
  unload/reload.
- [x] [015: retained-document model and revised Stage 2–3 acceptance](tasks/open/015-retained-document-model.md).
- [x] Execute [016–022 in the local retention batch](tasks/local-retention-batch.md):
  migration, checkpoints, real-editor undo proof, live adapter, closed-buffer UI,
  workspace resume and acceptance harness.
- [x] [023](tasks/open/023-retention-integration-review.md): record the missing
  018/021a decisions and correct runtime focus ownership. These are current
  Codex decisions under the user's continuation authority, with dated historical
  Astra evidence preserved.
- [x] [024](tasks/open/024-legacy-recovery-selection.md): explicit selection of
  preserved ambiguous legacy versions, including cancel, publication failure,
  secondary ownership, closed-buffer restart and source-byte preservation.
- [x] [025](tasks/open/025-shared-view-close-and-restore.md): shared-view detach,
  retired callbacks, failed preferred/all-owner restore, authoritative startup
  and native close routing.
- [x] Complete the post-implementation review against
  [Astra's handoff](docs/handoffs/2026-09-06-local-retention-review.md).
  Revised retention accepted; current scope/evidence and limitations are in the
  [2026-10-04 review](docs/evidence/retention-integration-2026-10-04.md).
- [x] [026: live workspace Execute Selection](tasks/open/026-live-workspace-execute-selection.md).
  Two owning workspaces and actual interpreters prove local Selection, loss,
  restart, stale rejection and source preservation. Native owner movement and
  visible application transfer refusal pass. See [accepted evidence](docs/evidence/workspace-selection-2026-10-04.md).
  This bounded slice does not accept all of Stage 4.
- [x] [027: live Selection assignments and broken-target correction](tasks/open/027-live-selection-assignments.md).
  Checked local chooser, sticky targets, visible broken state, reconnect,
  correction, live-only lifetime and native owner guards pass. See
  [accepted evidence](docs/evidence/selection-assignments-2026-10-05.md).
- [x] [028: live workspace cell/File/Main/Run-as-Script routes](tasks/open/028-live-workspace-run-variants.md).
  All editor variants use the invoking view's local resolver. Retained Main,
  save/cancel guards, Python restart and preserved IPython behavior pass in actual
  kernels. See [accepted evidence](docs/evidence/workspace-run-variants-2026-10-05.md).
- [x] Native completion/help/tool/Run/debugger request/result provenance is accepted through
  [029](tasks/open/029-native-request-result-provenance.md). Exact native echoes,
  held stale replies, script successor receipts and full peer/legacy controls pass.
  This completes the native provenance slice with 026–028. See [accepted evidence](docs/evidence/native-provenance-2026-10-05.md).
  Transitional shell migration remains deferred.
- [x] [030: real-kernel workspace-close acceptance](tasks/open/030-live-workspace-close-acceptance.md).
  Cancel, failed retention publication and fresh retry preserve both kernels;
  durable text/undo/views precede A-only teardown; A exits, B stays live and A
  resumes current retained views. Bounded intent/resume/placement/callback fixes
  pass. [Evidence](docs/evidence/workspace-close-2026-10-05.md) corrects the earlier
  broad 029 sign-off and completes local Stage 4 through 026–030.
- [x] Stage 5 through [031](tasks/open/031-workspace-debugger-and-breakpoint-ownership.md):
  durable independent breakpoint overlays, fixed debugger sessions, foreground
  controls, executable PM provenance and stale frame guards. Real A/B kernels,
  Cancel/failure/retry, disk retention before A-only teardown, B PM continuity
  and fresh-process overlay restore pass. [Evidence](docs/evidence/workspace-debugger-2026-10-06.md)
  records 481 tests/51 subtests, all 15 live controls and full peer/legacy smokes.
  Zombie workspaces and their reconciliation remain deferred.
- [ ] **NEXT — Stage 6: migrate tools, projects, preferences, history, capability
  fallbacks, and persistent workspace affiliation.**
  Follow [014 Stage 6](tasks/open/014-concurrent-workspace-implementation.md#6-tools-projects-preferences-history-and-affiliation).
- [ ] Stage 7: close external ingress, compatibility, scale, census, and full
  integrated acceptance obligations.

The historical Stage 2–3 entries keep their July evidence. The separate 015–025
entries record acceptance of revised September retention. Stage 4 is accepted
through 026–030 and Stage 5 through 031; Stage 6–7 work
and File Move/Fork UX remain pending; no TOAS/Rhizome integration is implied.

Accept and commit each stage independently. A later stage may not begin until
its dependency-stage acceptance and completion evidence are recorded in
Experiment 014.
