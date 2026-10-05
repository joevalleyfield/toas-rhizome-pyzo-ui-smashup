# 027: Live Selection assignments and broken-target correction

## Status

COMPLETE — accepted by Codex 2026-10-05 after executing the existing Experiment 014 Stage 4 NEXT gate
under “Take the next.” Depends on accepted 026 (root `8c458a4f`, Pyzo `3abb51c5`)
and coordinating root `c666da45`. The September amendment remains normative.

Accepted root implementation `58f689f709527bc819c13389d9230ea9e7a6b2d7` and
Pyzo `19d619a09667b92253d2c42c40903b356dcfa019`. See
[completion evidence](../../docs/evidence/selection-assignments-2026-10-05.md).

## Outcome and scope

Each live editor view can choose a same-workspace shell for Execute Selection,
Selection-and-Advance and print-current-line, or return to workspace-foreground
routing. Assignment survives ordinary focus changes and kernel restart. Unexpected
loss is visibly broken and cannot fall back. Reconnect repairs the same live
shell identity; confirmed closure resets to implicit. Retired/reopened views and
application restart do not inherit live assignments. A view transferred to another
owner retains a broken assignment until explicit correction, rather than silently
changing its target. Native within-owner rearrangement preserves assignment.

Provide a Run menu Selection-target chooser that shows only local eligible shells,
the checked implicit/explicit choice, and an unavailable assigned target. Menu
actions address the editor/view captured when the chooser opens and revalidate
its owner/epoch at activation. Other Run commands keep their existing behavior;
their current global-target display must not imply it controls peer Selection.

## Allowed write surfaces

- Root routing model, focused tests and a test-owned real-kernel assignment probe.
- Pyzo `core/workspaceExecution.py`, Run menu projection and focused tests;
  bounded application wiring only if required by these assertions.
  The chooser may live in a small `core/selectionTargetMenu.py` UI module with
  real-QMenu controls independent of global menu initialization.
  The real reconnect probe reproduced a queued old-connection close callback
  closing the newly connected context. A bounded `core/shell.py` connection-
  identity guard and focused callback tests are included to complete reconnect.
- This task, completion evidence and existing mutable queue references.

No all-Run migration, debugger/tool callback migration, File Move/Fork UX,
QtADS/binding or TOAS/Rhizome changes. No shell transfer/migration or zombies.

## Pre-edit state/assertion matrix

| State / ordering | Machine-checkable assertion | Known handling / gap |
| --- | --- | --- |
| Local explicit target; another local or foreign shell foregrounded | deliveries contain only assigned native shell; provenance mode explicit | Pure router supports; live bridge always requires/sends foreground (gap) |
| Explicit target eligible; local foreground absent/lost | resolved target equals explicit identity; no foreground dependency | Live resolver prematurely refuses (gap) |
| Unexpected target loss / restart pending / failed startup | broken mode and broken status; zero sends and visible correction text | Router supports; live UI/API missing |
| Same live shell reconnects / restart completes | same shell ID, new generation, explicit restored; old response rejected | Router supports; bridge dispatch still foreground-only (gap) |
| Broken target; foreground/replacement shell changes | remains broken; no send until reassign/clear/reconnect | Router supports; bridge gate/UI missing |
| Confirmed target close vs canceled native close | close resets implicit; cancel preserves exact assignment and token | Existing lifecycle calls detach only on commit; new controls needed |
| Clear or reassign current / broken view | current local target chosen; old token invalid unless effective route unchanged | Router supports; application operation missing |
| Foreign, starting/dead, unregistered or retired target | mutation refused; assignment/owners unchanged; status visible | Router + bridge admission; API missing |
| Closed/reopened view same ID, including close/reopen between sync calls | fresh implicit assignment; old operation/chooser context invalid | Registry epoch/record lifetime; bridge needs explicit lifetime handling |
| Live view owner/epoch changes; transfer away and back between sync calls | explicit becomes/stays broken; no foreign send; old operation invalid | Bridge currently closes/re-registers and silently drops assignment (gap) |
| Missing/retired editor, wrong document, unavailable workspace | no assignment mutation or send; disabled chooser / visible refusal | Existing admission reused; menu actions need captured context |
| Focus/editor changes while menu open; view moves/closes before action | action affects captured live view only, or refuses stale epoch | New menu context required |
| Local shell list eligible / empty / duplicate names / changed after popup | choices local only; check state unambiguous; stale native shell action refused | New menu controls |
| Two views of same resource; fresh application service | assignments independent; serialization unchanged; fresh service implicit | Live-only router state; new controls |
| Within-owner native float/redock | owner/shell/generation/assignment unchanged; actual delivery correct | 026 native movement seam; extend real proof |
| Legacy and File/Main/cell commands | existing target behavior/payload unchanged; labels describe scope | Existing controls plus menu test |
| Native Pyzo menu wrapper / shortcut settings | chooser has stable menu path; transient shell choices hidden from durable shortcut model | Live startup exposed wrapper gap; add real wrapper/key-map control |
| Current vs retired connection callback; replacement still preparing/failed | only current connection closes context/reports loss; retired callback performs zero context/UI calls | Actual reconnect stalls with new context disconnected; focused callback gate before fix |

The matrix identifies current gaps before source/test edits. The user's request
authorizes this next gate, its necessary assertions and implementation; no strict
external-validation mode is requested. Preserve the 026 no-fallback and stale
guards while adding explicit routing.

## Acceptance and completion

Focused service/router/menu controls must pass. A test-owned Qt app with two
workspaces and multiple actual kernels must use the menu to assign/correct,
demonstrate sticky delivery in both owners, restart/generation rejection, visible
broken loss without fallback, clearing/reassignment, native movement and confirmed
closure. Saved source bytes remain unchanged. Full peer/legacy Run/live-debug/
postmortem and retention controls remain green. Record exact root/Pyzo revisions,
meaningful before/after failures, test counts, limits and cleanup; commit the slice
before moving NEXT to the already-planned remaining Run/provenance gate.

## Completion

Run > Selection target now exposes workspace foreground and eligible local shell
choices with one checked assignment. Explicit targets survive local/foreign focus
changes and restart. Broken state remains visible until same-shell reconnect,
reassignment or clearing. Actions retain and validate the captured native view;
closed/reopened views default to implicit. Owner/epoch drift breaks existing
assignment intent, and both admission and dispatch verify native ownership.
Assignments remain live-only and absent from document persistence.

The real app proof uses three initially live interpreters across A/B, an actual
restart and another connection generation, then repeat transport loss. It verifies
namespaces 11/22, chooser-based correction to the other A shell, clearing, canceled
and confirmed shell close, movement, retained same-ID native view reopening,
unchanged source bytes and stale-generation result rejection. A queued retired
broker callback originally closed the replacement context; the native identity
guard fixes this without changing current disconnect reporting. Live connection
recovery is exercised through `connectToKernel`; this does not add a new reconnect
button or a shell-migration feature.

Final coordinated suite: **381 passed, 12 skipped, 45 subtests**, 2.41s.
**11 live controls passed**, 35.39s (assignment probe 3.956s; prior Selection probe
3.449s). Full peer **11.531s**, legacy **7.321s**. Focused Run/bridge/menu/connection
controls: 54 passed; router: 12 passed. Eleven skips are opt-in live controls run
separately; the remaining stock tab-edge skip and two Qt high-DPI warnings remain.
Touched Python compilation, Ruff name/import diagnostics and added-line whitespace
checks pass. No QtADS/binding or TOAS/Rhizome changes; nothing pushed.

Full Stage 4 remains pending. NEXT is the existing remaining Execute/cell/File/
Main/Run-as-Script routing gate, followed by complete native request/result
provenance. Debugger ownership and tools stay in their later stages; the September
deferrals remain unchanged. The offscreen native replay does not claim physical
macOS drag/accessibility or Windows/Linux portability acceptance.
