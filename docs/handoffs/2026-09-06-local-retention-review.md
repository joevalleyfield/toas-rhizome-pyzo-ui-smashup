# Astra self-handoff — local retention review

Current continuation, 2026-10-04: **retention batch accepted by Codex** under the
user's continuation authority after 023–025 and the expanded live/application
controls. The September amendment remains normative; no historical Astra decision
is invented. See [current evidence](../evidence/retention-integration-2026-10-04.md).
Next is the bounded live Execute Selection slice 026. Full Stage 4, File Move/Fork,
workspace debugging and contextual tools remain pending; migration/zombies remain
deferred.

Historical review, 2026-09-23: **022 accepted** at root `d50c07af` / Pyzo `776cf29c`.
Independent verification passes 7 live tests and 282 combined tests (8 skips).
The final resolution-durability blocker is closed by forced-exit/restart
verification. See the final 022 integration-review section. The harness task is
COMPLETE; broader retention-batch integration and Stage 4 acceptance are not
granted by this bounded review.

Recorded 2026-09-06 for resumption after Luna's implementation batch, or earlier
when a task needs architectural review. This is a durable project handoff, not
an automation or a scheduled wake-up.

## Location and authority

Workspace: `/Users/tim/Documents/Projects/toas-rhizome-pyzo-ui-smashup`.
Conversation carrying the decisions: `01a078fe-8d72-7d93-884b-e448ef3598dd`.
Start with [the amendment](../local-workspace-scope-2026-09-06.md),
[the batch](../../tasks/local-retention-batch.md), and
[the execution checklist](../../EXECUTION_CHECKLIST.md). The amendment overrides
conflicting July text; do not resurrect frozen workspace text, shell migration,
or zombies from the historical acceptance sections.

The user's priority is reliable local editing: several optional-folder
workspaces, shared documents, continuous retention including undo/view state,
close as suspended participation, and source writes only through explicit
operations. Portability and distributed synchronization are deferred. The user
expects engineering judgment, not another exhaustive requirements interview.

## Starting evidence and cautions

Before this docs commit, root parent was `57cedcd2`, Pyzo's reported revision
was `e46e1cf`, binding `eb29ef0`, embedded QtADS `244157d`. Verify actual
revisions at resumption; do not rely on these as immutable pins. The new docs
commit can be located by description `Define Luna retention tasks and Astra review handoff`.

Hidden QMainWindow removal was accepted in Experiment 012; peer mode chooses a
QObject despite the remaining MainWindow class name. Stage 4's pure router is
implemented but actual Pyzo Run still needs migration. One full peer replay
passed after several lifecycle assertion failures. The projector correction is
not established as a cure for the intermittent failure. Existing task notes
contain conflicting plugin/smoke claims; use captured runtime evidence.

The repaired venv lives at `deps/pyzo/.venv`; its prior copy was preserved under
`/tmp/pyzo-venv-before-rebuild`. Use the local wheel and isolated settings.
Do not alter the separately symlinked TOAS/Rhizome repositories. Prefer JJ.

## Intermediate review: task 018

Read its executable proof and evidence before authorizing 019. Confirm real
Pyzo transaction grouping, two-view synchronization, persistent undo/redo after
widget destruction/restart, and absence of private Qt assumptions. If the proof
fails, make the adapter decision here and write a narrowly bounded follow-up;
do not let Luna weaken retention guarantees to get a green result. Record the
review decision, reasoning, and reviewed revision in 018 and 019.

## Post-implementation review

- Read completion evidence and independently inspect actual root/Pyzo commits
  for 015–022. Task completion is not integration acceptance.
- Verify the last-view/untitled/closed-buffer workflow and A/B suspend/resume with
  real widgets and separate processes. Ensure A never revives stale text merely
  because it was closed, and closing both workspaces keeps unsaved state reachable.
- Verify ordinary undo grouping, persistent undo/redo, view positions, text
  metadata, Save/Discard separation, external conflict handling, and legacy
  snapshot preservation. Check that ambiguous migrated records require a visible
  choice while unrelated documents can open.
- Verify checkpoint deadlines/completion latency, stale-write exclusion,
  crash-after-checkpoint recovery, and failure-before-destructive-close ordering.
  Check sustained-edit responsiveness and history/storage growth.
- Verify live shell close cancellation, explicit termination warnings, rejected
  cross-workspace shell moves, and preserved Run/live-debug/postmortem behavior.
- Inspect smoke logs and child exit codes; resolve or explicitly leave open the
  intermittent projector failure. Do not promote a single pass to a root-cause fix.
- Validate docs against delivered behavior, correct stale status claims, and
  update dependency runtime/revision evidence after observing it. Preserve dated
  earlier acceptance, do not overwrite history with new claims.

Record findings in `docs/evidence/local-retention-integration-review.md` with
accepted/rejected criteria and exact revisions. If accepted, mark the retention
batch accepted and return the checklist to the smallest live Stage 4 routing
slice. File move/fork UX and later ordinary workspace debugger/tool/ingress work
remain explicit pending scope. If rejected, create bounded corrections; do not
reopen portability or authorize TOAS integration implicitly.

## Completion ledger

The original September ledger was pending. Dated reviews below preserve the
implementation history. The October continuation closes the current 018 gate
and retention integration decision in the linked current evidence.

2026-09-20: [Independent 022 review](../evidence/local-retention-integration-review.md)
at root `2e9ab32d` / Pyzo `f377bfde` reproduced five passing live tests and the
zero-open restart sequence, but identified four acceptance gaps. 022 remains
`REVIEW_REQUIRED`; final batch integration acceptance has not been granted.

2026-09-21: Second independent review at root `59f94bf3` / Pyzo `0c5c3f20`
accepts failure/close-refusal/retry and persistent zero-open coverage. External
conflict on ordinary retained restore and meaningful latency/storage metrics
remain open; reproduction and correction scope are in the same review document.
022 remains `REVIEW_REQUIRED`.

2026-09-23: Resolution durability is corrected. The shared resolution now
notifies automatic retention; a test-owned crash after the durable revision and
fresh restart restore the resolved text with conflict cleared. The live matrix
passed 7/7 and the combined suite passed 282 with 8 skips. 022 remains
`REVIEW_REQUIRED` pending final acceptance.

2026-09-23: The unresolved-conflict lifecycle correction is implemented and
verified. Original and later external observations persist separately across
restart; explicit document-owned resolution clears the conflict and updates
all shared views. The live matrix passed 7/7 and the combined suite passed 282
with 8 skips. 022 remains `REVIEW_REQUIRED` pending final acceptance.

2026-09-21: The bounded corrections are implemented and verified: ordinary
retained-document external conflict is detected without legacy recovery
seeding, and sustained checkpoint metrics cover per-revision latency, writes
during editing, multiple history entries, and the full persistence tree. The
live matrix passed 7/7; the combined suite passed 281 with 8 skips. 022 remains
`REVIEW_REQUIRED` pending acceptance.

2026-09-22: Third-review corrections are implemented. Document conflict
metadata persists across registry snapshots, source-encoding detection accepts
Latin-1 Python files safely, and the sustained metric control uses automatic
checkpoint scheduling with coalesced edit timing. The live matrix passed 7/7;
the combined suite passed 281 with 8 skips. 022 remains `REVIEW_REQUIRED`.

2026-09-22: Third independent review at root `8da4d712` / Pyzo `a48eca2d`
reproduced the passing suites but withheld acceptance. Conflict persistence/
reconciliation and automatic latency measurement remain incomplete; a new
UTF-8-only decoding regression is reproduced at method level. Full findings
and correction scope are in the integration review. 022 remains `REVIEW_REQUIRED`.

2026-09-22: Fourth review at root `b7849976` / Pyzo `86f6c70a` accepts the
encoding and automatic-scheduling corrections. One conflict-lifecycle blocker
remains: the restore detector overwrites unresolved persisted observations and
can clear conflict state without explicit reconciliation. The focused
reproduction and remaining acceptance test are in the fourth review section.
022 remains `REVIEW_REQUIRED`.
