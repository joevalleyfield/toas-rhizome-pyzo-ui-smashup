# 021 prerequisite review and execution order

Date: 2026-09-18. Intended executor: Luna, sequentially in this checkout.
Authority: the user's request for actionable prerequisite slices, the
[September amendment](../docs/local-workspace-scope-2026-09-06.md), and the
[batch contract](local-retention-batch.md).

## Finding and disposition

Luna reported reaching 021's stop boundary without changing files. Inspection
confirms one startup backend/model pair, owner-singular editor host and close
callbacks, one `PeerApplicationController.workspace`, and one
`pyzo.workspaceSession` capture/restore route. Retained reopen rejects another
workspace identity. The coordinator's support for multiple models does not
provide a second rendered, correctly routed workspace.

Resolve this runtime integration gap in order:

| Task | Observable result |
| --- | --- |
| [021a0](open/021a0-runtime-chrome-reconciliation.md) | Runtime-owned frame chrome reconciles exactly across QtADS recreation. |
| [021a1](open/021a1-runtime-startup-teardown.md) | Isolated startup and smoke teardown are bounded and non-interactive. |
| [021a](open/021a-workspace-runtime-ownership.md) | Existing single-workspace behavior uses an explicit runtime owner. |
| [021b](open/021b-live-workspace-routing.md) | Two real runtimes render and route shared editor views correctly. |
| [021c](open/021c-workspace-set-persistence.md) | The loaded set survives restart; minimal named workspace commands work. |
| [021](open/021-workspace-suspend-resume.md) | Individual workspace close/resume safely suspends participation. |
| [022](open/022-local-retention-acceptance-harness.md) | End-to-end acceptance of the combined workflow. |

## First action and dispatch

020 is complete with evidence at
`docs/evidence/task-020-local-retention.md`, root revision `4ed8b1b3`, and Pyzo
revision `34b10468`. Do not reopen its acceptance while executing these
prerequisites.

The existing 021a runtime-extraction checkpoint is Pyzo revision `30a01e5a`.
Claim 021a0, complete 021a1, and resume 021a only after each preceding slice is
evidenced and committed. Each evidenced, committed completion unlocks only the
next slice; updating that next task's dependency status is authorized.
These slices resolve 021's missing-seam review for their explicit write surfaces.
No further approval is required within that scope once dependency gates pass.
Run one task at a time; do not launch overlapping workers.

## Common architectural constraints

- Keep one application document registry, editing/undo authority and checkpoint
  coordinator. Each runtime owns its backend/manager, model, frame/host lookup,
  session adapter and workspace-local state. Reuse existing coordinator identity;
  do not introduce a competing workspace registry or application controller.
- Resolve ownership from explicit workspace identity or the initiating pane/view.
  Foreground workspace may resolve an unscoped action once at entry; changing
  focus cannot retarget an in-flight callback. Reject stale/unavailable owners.
- Explicit, tested compatibility accessors are acceptable. Rebinding global
  workspace/backend/editor objects on focus changes is not.
- Preserve shell/tool ownership. An action exposed with multiple workspaces must
  route correctly or be visibly unavailable, never silently act in another
  workspace. Full Stage 4 execution and contextual tool/settings integration
  remain outside this batch's acceptance.
- Use separate QtADS managers and existing peer frames/services. No new windowing
  framework, binding changes, shell migration, zombies, or document-browser redesign.
- Follow the batch's isolated real-Qt tests and JJ commit rules. Evidence includes
  actual commands/results, failures, smoke logs, separate root/Pyzo revisions,
  limitations and the next eligible task. Model-only tests are insufficient.
- If writes beyond a task's allowance become necessary, return the smallest
  reproduction, required file/seam, and proposed expansion. Do not broaden silently.

## Handoff to Luna

Read this review and the batch contract. Execute 021a0, 021a1, 021a, 021b, and
021c in sequence, with an evidence/commit gate after each. Resume 021 after
021c passes. These are planning changes; no implementation or passing tests are
claimed here.
