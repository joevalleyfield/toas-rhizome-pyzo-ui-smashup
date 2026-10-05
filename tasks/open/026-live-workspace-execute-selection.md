# 026: Route Execute Selection through the invoking workspace

## Status

COMPLETE — accepted 2026-10-04 under the user's instruction
“Take the next item.” Starting root `18de8d05`, Pyzo `ed7cfb86`; both clean.
This is Experiment 014 Stage 4's first live slice under the September amendment.
The bounded Selection slice is accepted; full Stage 4 acceptance remains pending.

Root implementation `8c458a4fa32eedf2fc6b6d866a265ef02429a590`;
Pyzo implementation `3abb51c5ffaad46d7d6053c9e32bada071eaa664`.
See [completion evidence](../../docs/evidence/workspace-selection-2026-10-04.md).

## Outcome

Two real workspaces each own a live shell and can Execute Selection into their
own interpreter. Invoking an editor in A while a shell in B was most recently
foregrounded must not send A's code to B. Use the existing pure execution router
and preserve the legacy single-workspace route.

## Allowed surface

Root execution model/probe/tests; Pyzo shell runtime creation and registration,
application execution service, RunCommandService selection path, focused tests;
this task and linked evidence. Do not migrate all Run variants, breakpoints,
tools or preferences in this slice. No QtADS/binding or TOAS/Rhizome changes.

## State/assertion gate before implementation

- Invoking view belongs to A/B, or is retired/unavailable; never capture an
  operation from the compatibility primary alias when its owner is known.
- Local foreground shell is eligible, absent, lost, or recycled. Foreground
  recency in another workspace must not create a fallback queue.
- Captured view/shell identity and kernel generation may remain current or
  become stale between invocation and dispatch/completion.
- Native pane/frame movement within an owner preserves shell identity;
  cross-workspace transfer is visibly refused.

Encode delivery counts and values in two actual kernel namespaces, captured
workspace/view/shell identities, source bytes unchanged by Execute Selection,
no send on an ineligible or stale target, and a visible explanation on refusal.
Map every case to a meaningful assertion before changing the routing boundary.

## Acceptance

The real two-kernel probe verifies A/B routing in both focus orders, no local
shell, target loss, recycle, stale result rejection, and source-byte preservation.
Focused router/service controls and full peer/legacy Run/live-debug/postmortem
controls stay green. Commit the bounded slice and record revisions and remaining
Stage 4 gates: explicit assignment UI, broken-target correction, all Execute and
File/Main variants, and complete operation provenance. Shell migration and
zombies remain deferred. File Move/Fork UX remains a later explicit local slice.

## Pre-edit coverage map and implementation boundary

The user's instruction authorizes proceeding with this task and its stated
matrix. Engineer/state-assertion-fix-gate apply; no external validation mode.

| State | Assertion | Coverage / current gap |
| --- | --- | --- |
| Editor A/B; other workspace shell most recently focused | `calls[owner] == [payload]`, `calls[other] == []` | Run service/live two-kernel proof; currently global shell routing |
| Statement vs multiline selection; advance/print-line variants | source/line payload and captured editor unchanged | Focused Run test; legacy extraction preserved |
| No local foreground shell; starting/dead/disconnected shell | no sends; visible refusal | Bridge test/live no-target/loss; no bridge yet |
| Local target lost with an older local shell still alive | no recency fallback send | Pure router test + bridge test |
| A shell owned by another workspace | registration/dispatch refuse; owners unchanged | Bridge/native host test |
| Shell restart pending/failed/ready | no send pending; same live shell ID, new generation on ready | Bridge/live actual restart |
| Close/reopen same view ID; owner transfer; unavailable workspace | old operation not current; no stale send | Registry epoch + router + bridge tests |
| Focus changes after capture; shell close/loss/recycle before dispatch | `dispatch(old) is False`, delivery counts unchanged | Bridge tests/live stale captured operation |
| Current vs stale operation response | consumer called only for current token | Bridge tests/live tagged kernel response |
| Native within-workspace float/re-dock | same shell/context/owner and current token | Real probe |
| Cross-workspace shell transfer | refused result/status; both layouts, IDs/context unchanged | Existing coordinator refusal + application bridge/native probe |
| Secondary shell metadata and explicit closure | owner model title equals native title; only owner's pane removed; old operation rejected | Live probe / remaining primary-model metadata gap |
| Legacy non-peer and File/Main routes | original global target/payload | Existing focused and full peer/legacy controls |

Known proof gap: re-registering a retained view at router epoch 1 could admit an
old token. The bridge must register the resource registry's actual view epoch.
No router transitional-shell migration is wired into the live service.
Allowed new module: Pyzo `core/workspaceExecution.py` and corresponding focused
tests. This is the application execution boundary already allowed above.

## Completion evidence

Execute Selection, Selection-and-Advance and print-current-line now resolve the
invoking live view's owner, capture shell/kernel-generation provenance, and
revalidate immediately before sending. Foreign workspace focus cannot redirect
these commands. New shells use the active runtime's native manager, ownership
map and lifecycle. Secondary shell metadata and explicit closure use that owner.
Native restart retains shell identity and advances generation; lost/closed
foreground targets cannot choose an older eligible shell automatically.

The real test-owned Qt probe verifies values 101/202 in separate kernel
namespaces in both focus orders, statement and multiline payloads, no-local-shell
refusal, actual restart, disconnected newest target while older A stays alive,
rejected stale operations and tagged results, retired editor refusal, secondary
shell closure, native float/redock identity, visible transfer refusal and unchanged
source bytes. Transfer refusal is tested at the application/coordinator seam;
native macOS cross-manager dragging is not claimed.

Final combined suite: **344 passed, 11 skipped, 45 subtests**, 2.30s. Ten opt-in
live controls pass separately (30.60s); final Selection replay after closed-shell
reference cleanup passes in 3.745s. Full peer and legacy controls pass in 11.220s
and 7.377s. Focused final Selection/bridge controls: 19 passed. Compilation,
name/import diagnostics and added-line whitespace checks pass. The two existing
Qt high-DPI deprecation warnings remain.

The NEXT marker returns to the existing Stage 4 assignment/broken-target gate.
All other Execute/File/Main/Run-as-Script routing and native completion/help/tool/
debugger callback provenance remain later gates. The result-consumption seam is
proved with a real prior-generation result; it does not migrate those callbacks.
File Move/Fork UX, Stage 5 debugger isolation and Stage 6 tools remain pending.
Shell migration, zombies, portable synchronization and broad TOAS/Rhizome work
remain deferred. No QtADS/binding or TOAS/Rhizome changes; nothing pushed.
