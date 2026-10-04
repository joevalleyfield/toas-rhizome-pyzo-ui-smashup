# 021a: Extract explicit live workspace runtime ownership

## Status

COMPLETE — owner Codex; independently reconciled 2026-10-04 after 021a0/021a1
and a bounded focus-routing correction. Current runtime tests cover partial
construction cleanup and idempotent disposal; real peer startup/lifecycle,
two-runtime routing, and retained restart controls pass. See
[current integration review](../../docs/evidence/retention-integration-2026-10-04.md).
Dependency 020 is complete with committed root/Pyzo revisions and evidence.
Follow the [prerequisite review](../021-runtime-prerequisites.md) and
[batch contract](../local-retention-batch.md).

## Outcome

Assemble the current single workspace through a reusable runtime factory. All
workspace-bound callbacks refer to its owner; ordinary startup still loads one
workspace in this slice.

## Read before editing

Pyzo `core/main.py` startup, host creation, focus, metadata and close callbacks;
`core/applicationController.py`, `core/editorGroups.py`, `core/shellGroups.py`;
root coordinator, session, backend and application-lifecycle modules below.
Inspect callers before choosing compatibility accessors.

## Allowed writes

Pyzo `pyzo/core/main.py`, `applicationController.py`, `editorGroups.py`,
`shellGroups.py`, new `workspaceRuntime.py` in that directory, and focused tests.
Root `spikes/peer_frames/workspace_coordinator.py`, `workspace_session.py`,
`application_lifecycle.py`, `qtads_backend.py`, and matching tests, only for
runtime extraction adapters. This task's status/evidence at
`docs/evidence/task-021a-workspace-runtime.md` and 021b dependency status.

Complete [021a0](021a0-runtime-chrome-reconciliation.md) and
[021a1](021a1-runtime-startup-teardown.md) before claiming this task complete.

## Implementation contract

- Extract backend/model, frame/host lookup, session service and connection cleanup
  into an explicit live runtime keyed by the coordinator's stable identity.
- Keep document/undo authority, retention, application commands and the application
  controller outside the factory; runtime creation cannot reset them.
- Bind editor/shell creation, pane registration, focus, metadata, dialog-parent
  lookup and close callbacks to their runtime. Include default-frame creation
  and empty-frame recovery in the ownership audit.
- Partial construction cleans up its own widgets/connections/registrations;
  disposal cannot destroy shared document or retention services.
- Inventory remaining singular callers and assign them to 021b or 021c in the
  evidence. Document the factory and runtime lookup API for the next slice.

## Acceptance

- Real single-workspace startup, editor creation, tab/frame close, retained reopen,
  default-frame recreation, save/restart and shell-close cancellation preserve
  existing behavior. Preserve 020 non-final/final-view and discard coverage.
- Inject construction failure after partial registration: no orphan dock,
  coordinator entry, duplicate callback, or lost retained document remains.
- Verify owner-bound callbacks and exactly-once cleanup with the extracted runtime.
- Run focused controller/host/lifecycle/session tests and isolated real-editor
  smoke checks. Record actual results and separate root/Pyzo revisions.

## Stop boundary

Do not expose concurrent workspace commands, implement suspend/resume, or rewrite
storage here. A required QtADS redesign or wholesale editor replacement returns
REVIEW_REQUIRED with the smallest failing case and missing seam.
