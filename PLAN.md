# Feasibility Plan

This plan turns [REQUIREMENTS.md](REQUIREMENTS.md) into a sequence of
experiments. Each experiment should reduce one major uncertainty before the
next layer is attempted.

The experiment descriptions below are stable architecture and evidence
references. Use [EXECUTION_CHECKLIST.md](EXECUTION_CHECKLIST.md) as the mutable
work order when inserted experiments or discoveries make numeric order
ambiguous.

## Phase 0 — Establish the baseline

Run the assembled Pyzo checkout on macOS and document its current Qt binding,
editor/container architecture, run workflow, and live/post-mortem debugging
behavior. The result is a baseline against which every later experiment can be
compared.

## Phase 1 — Prove the docking mechanism independently

Build the smallest docking spike that demonstrates the required Visual
Studio-like interactions: multiple editor-like widgets, nested splits, floating
groups, drag-and-drop rearrangement, and re-docking. Confirm the binding and
build path are compatible with Pyzo's Qt stack before modifying Pyzo.

## Phase 2 — Prove multiple editor groups inside Pyzo

Introduce the smallest Pyzo-local change that permits more than one visible
editor group while preserving document tabs and ordinary editing. Demonstrate
that groups can be split, floated, moved, and re-docked without losing document
or editor state.

## Phase 3 — Define the application/backend seam

Specify a small, technology-neutral contract between the application-owned
workspace service and a docking backend. The contract must describe peer
frames, pane identity and placement, active context, close negotiation, and
layout persistence without exposing a main window or QtADS object.

Build a deterministic contract harness before adapting either Pyzo or QtADS.
This gives every later experiment the same observable operations and
invariants.

## Phase 4 — Replay the docking experiments through the seam

Repeat the successful standalone docking experiments through a QtADS adapter:
tabbing, local and outer splits, floating, cross-frame movement, overlapping
frame targeting, frame closure, and restoration. Deliberately exercise the
first pane and last pane of every frame so root/floating asymmetries cannot be
hidden by the happy path.

Run this phase in escalating slices:

1. Stock QtADS with a private privileged root.
2. A narrow adapter with PySide-level policy hooks.
3. The smallest necessary QtADS source changes when an invariant cannot be
   implemented above the library.

Each failed invariant must be attributed to application policy, adapter
design, binding exposure, or QtADS internals before source is forked.

## Phase 5 — Replay the Pyzo integration experiments

Project Pyzo's editor, shell, file browser, and run/debug surfaces as pane types
behind the same contract. Moving, grouping, or closing a frame must not transfer
ownership of documents, interpreters, or debugger state to the docking backend.

Exercise document and shell lifecycle independently from placement, including
dirty-document close negotiation and protection of running shells.

Before continuing deeper application-chrome work, run the per-group tab-edge
experiment. Preserve Pyzo's useful editor/tool distinction while generalizing
it: each tab group may independently place its tabs on the top, bottom, left,
or right. The setting belongs to application layout state rather than a global
QtADS flag or a pane type.

This experiment must establish the smallest QtADS fork surface because stock
QtADS exposes only a global top/bottom choice and implements tab layout and drag
geometry horizontally. Complete the standalone docking proof before projecting
the choice into Pyzo commands and defaults.

## Phase 6 — Preserve post-mortem re-entry

Exercise the complete post-mortem workflow after an unhandled exception:
re-enter the captured session, select a stack frame, navigate to its source,
and execute live interpreter code against that frame. Repeat after layout
changes, including movement between peer frames, floating, and re-docking.

## Phase 7 — Bound the fork and decide feasibility

For every required deviation, identify the narrowest owning layer and record
the exact Pyzo, binding, or QtADS source surface involved. Run the full
acceptance workflow, record portability risks for Windows and Linux, and decide
whether the stack is viable unchanged, viable with bounded forks, or unsuitable
for the peer-frame application model.

## Phase 8 — Remove the hidden Pyzo application host

After feasibility is accepted, replace the temporary hidden `QMainWindow` with
an application controller and narrow services. Migrate behavior-bearing menus,
Run/Debug routing, peer workspace persistence and named views, dialog/tool
parenting, metadata, appearance, and startup in independently accepted slices.

Peer-mode completion requires a runtime assertion that no `QMainWindow` exists,
while the complete editor/shell/file-browser/debugger/lifecycle workflow and
the legacy non-peer control remain green. This cleanup precedes toas/rhizome
integration and does not authorize it.

## Phase 9 — Ground concurrent workspace semantics and state ownership

After hidden-main removal, audit every persisted and live Pyzo state entry
point before splitting application state. Separate current storage scope from
effective semantic scope and record workspace, view, shared-resource, mixed,
and true application ownership without beginning migration.

Turn that census into an explicit concurrent-workspace requirements baseline,
then analyze technical risk before implementation. The resulting requirements
and risk artifacts are normative inputs to the implementation plan; neither
the audit nor risk analysis authorizes source changes.

## Phase 10 — Implement concurrent workspaces through proof gates

The [2026-09-06 local workspace amendment](docs/local-workspace-scope-2026-09-06.md)
supersedes conflicting July scope. The October retention integration review
resolves Stage 2–3's revised gate through tasks 015–025, including explicit legacy
recovery selection and shared-view close/restore corrections.
[026: live workspace Execute Selection](tasks/open/026-live-workspace-execute-selection.md)
is accepted as the first bounded live Stage 4 slice.
[027: live Selection assignments](tasks/open/027-live-selection-assignments.md)
adds the checked local chooser and broken-target correction.
[028: workspace Run variants](tasks/open/028-live-workspace-run-variants.md)
accepts cell/File/retained Main and script save/restart routing.
[029: native request/result provenance](tasks/open/029-native-request-result-provenance.md)
closes native callbacks, caches, transport and script successor receipts.
[030 closure evidence](docs/evidence/workspace-close-2026-10-05.md) supplies the
missing integrated two-kernel cancel/failure/termination/resume proof and bounded
repairs, correcting 029's broad sign-off. This completes local Stage 4 through
026–030. [031 Stage 5 evidence](docs/evidence/workspace-debugger-2026-10-06.md)
accepts durable independent overlays, fixed live/PM ownership and stale frame
provenance, conservative closure and fresh-process restoration.
[032 Stage 6 evidence](docs/evidence/workspace-tools-2026-10-06.md) accepts the
final ownership census, independent contextual state, ten built-in tools,
capability reporting, extension compatibility and pane affiliation. The next
gate is existing Stage 7 external ingress, compatibility, scale and integrated
acceptance, including final global-context census and physical/platform controls.
Portable workspaces, synchronization, live shell migration and zombies remain
deferred. Historical stage evidence keeps its original dates and contract.

Implement the accepted model through the independently committed stages in
[Experiment 014](tasks/open/014-concurrent-workspace-implementation.md):

1. durable identity and explicit workspace context;
2. shared document resources and workspace-owned views;
3. versioned persistence, recovery, and workspace lifecycle;
4. workspace execution routing, explicit/broken targets and shell-transfer refusal;
5. breakpoint overlays, debugger ownership and terminate-or-cancel closure;
6. tools, projects, preferences, history, and affiliation; and
7. external ingress, compatibility, scale, and integrated acceptance.

Each stage must satisfy its risk-reduction evidence before the next dependent
stage begins. Single-workspace behavior remains a specialization of the new
model, and peer, vanilla, and legacy QtADS controls remain acceptance gates.
Deferred capabilities may not enter implicitly merely because a touched layer
could support them.

## Ordering rule

Do not begin toas or rhizome UI integration until Phase 6 succeeds or produces
a clearly bounded blocker. Do not infer peer-frame feasibility from a visually
similar QtADS layout: the contract and lifecycle invariants must pass. The first
decision is whether Pyzo and the selected docking backend can support the
required editor, lifecycle, and debugging model; the later product shape
depends on that answer.
