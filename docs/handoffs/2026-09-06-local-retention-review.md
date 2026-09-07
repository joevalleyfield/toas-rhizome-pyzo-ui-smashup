# Astra self-handoff — local retention review

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

Pending. Luna records per-task evidence and revisions in each task. Astra records
the 018 gate and final integration verdict here when performed.

