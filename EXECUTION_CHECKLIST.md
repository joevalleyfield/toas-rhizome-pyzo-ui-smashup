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
- [ ] Reconcile [Experiment 003 — Pyzo editor groups](tasks/open/003-pyzo-editor-groups.md)
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
- [ ] **NEXT — Cause an unhandled exception and re-enter its captured post-mortem session.**
- [ ] Select stack frames and navigate source without a privileged frame.
- [ ] Execute live interpreter code against the selected captured frame.
- [ ] Repeat after split, float, cross-frame move, re-dock, and relevant frame
  closure.
- [ ] Verify breakpoints, traceback navigation, shell state, and debugger context
  survive the complete workflow.

Do not begin toas or rhizome UI integration before this section passes or
produces a clearly bounded blocker.

## 6. Bound forks and portability obligations

Reference: [Experiment 010 — fork boundary](tasks/open/010-fork-boundary.md).

- [ ] Attribute every deviation to application policy, peer adapter, Pyzo,
  PySide6-QtAds binding, or QtADS source.
- [ ] Decide whether hidden `QMainWindow` removal is required, optional cleanup,
  or blocked by a specific Pyzo service assumption.
- [ ] Record exact maintained fork revisions and likely upstreamable slices.
- [ ] Run or explicitly schedule Windows and Linux tests for docking, menus,
  shortcuts, focus, high-DPI, and lifecycle.
- [ ] Confirm macOS-first choices did not require amputating Windows/Linux
  support.

## 7. Make the integrated feasibility decision

Reference: [Experiment 005 — feasibility decision](tasks/open/005-feasibility-decision.md).

- [ ] Replay the full editor, shell, file-browser, run/debug, post-mortem,
  lifecycle, layout, and command/menu acceptance workflow.
- [ ] Classify the stack as viable unchanged, viable with bounded maintained
  forks, or unsuitable for the peer-frame application model.
- [ ] Record the recommendation and prerequisites for any subsequent
  toas/rhizome transcript-editor integration.
