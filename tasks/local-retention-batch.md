# Local retention implementation batch

Date: 2026-09-06. Parent: [Experiment 014](open/014-concurrent-workspace-implementation.md).
Authority: [local workspace scope](../docs/local-workspace-scope-2026-09-06.md).

## Purpose and dispatch

Implement the revised local document-retention and workspace-resume behavior
before resuming Stage 4 execution integration. This batch does not implement
TOAS, portability, synchronization, shell migration, zombies, or the remainder
of Stage 4. File-move/fork command UX remains a later bounded slice under the
amendment; it is not silently claimed complete by this batch.

Current status, 2026-10-04: **retention integration accepted** after 023–025.
See [current evidence](../docs/evidence/retention-integration-2026-10-04.md).
The 018/021a missing decisions are now explicitly recorded as current Codex
reviews; they are not retroactive claims of Astra approval. All tasks in the
historical table below are complete. Next: [026](open/026-live-workspace-execute-selection.md).

The table records the original September dispatch dependencies. Initially only
015 was READY; successors waited for their named gates. Runs stayed sequential
because source surfaces overlap. These constraints remain useful when reviewing
the history, but do not represent the current queue.

| Task | Outcome | Unlock condition |
| --- | --- | --- |
| [015](open/015-retained-document-model.md) | Retained documents and revised acceptance contract | Ready now |
| [016](open/016-retained-state-storage-migration.md) | Versioned retained-state storage and conservative migration | 015 complete |
| [017](open/017-retention-checkpoint-coordinator.md) | Automatic checkpoint scheduling and durability barrier | 016 complete |
| [018](open/018-qt-undo-retention-proof.md) | Real-editor undo retention feasibility proof | 017 complete |
| [019](open/019-live-document-retention-adapter.md) | Wire the approved retained-document editor adapter | 018 accepted by Astra |
| [020](open/020-retained-buffer-close-reopen.md) | Retain closed buffers and expose reopen UI | 019 complete |
| [021a0](open/021a0-runtime-chrome-reconciliation.md) | Reconcile runtime-owned frame chrome across QtADS recreation | 020 complete |
| [021a1](open/021a1-runtime-startup-teardown.md) | Bound isolated startup, timer, and teardown behavior | 021a0 complete |
| [021a](open/021a-workspace-runtime-ownership.md) | Extract explicit live runtime ownership | 021a0 and 021a1 complete |
| [021b](open/021b-live-workspace-routing.md) | Render and route two live workspaces | 021a complete |
| [021c](open/021c-workspace-set-persistence.md) | Persist/restore the loaded set and expose minimal commands | 021b complete |
| [021](open/021-workspace-suspend-resume.md) | Suspend and resume workspace participation | 021c complete |
| [022](open/022-local-retention-acceptance-harness.md) | End-to-end retention acceptance and review evidence | 021 complete |

The 2026-09-18 [prerequisite review](021-runtime-prerequisites.md) records the
single-runtime blocker and execution instructions for 021a–021c. It historically required reconciliation of 020's completion evidence before
runtime work. The October review closes that sequence; no single two-view
follow-up commit was treated as complete batch acceptance. The slices are sequential prerequisites, not Stage 4 expansion.

## Executor contract

- Claim one READY task by recording owner, start date, and starting root/Pyzo
  revisions in its Status. Read project instructions and the Engineer skill.
  For risky lifecycle/persistence fixes, apply the state-assertion-fix-gate
  instructions before edits. Use the task's acceptance matrix as the boundary.
- Inspect JJ status and diffs in each touched repository. Preserve unrelated
  changes. Root coordinates code under `spikes/`; Pyzo has an independent repo
  under `deps/pyzo`. Do not edit TOAS, Rhizome, QtADS, or the binding fork.
- Implement only the allowed surfaces. New modules explicitly allowed by a task
  may be imported/re-exported through the nearest package initializer as needed.
  A required edit elsewhere must be reported with its reason before expanding.
- Use Python 3.12 through `.codex-local/bin/uvt` so `UV_PROJECT_ENVIRONMENT`,
  `UV_CACHE_DIR`, and Python caches stay outside the cloud-synced checkout.
  Otherwise use `deps/pyzo/.venv/bin/python` directly only as a compatibility
  fallback.
  Inspect the environment before repair; network/escalation may be needed.
- Use the prebuilt wheel at
  `deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl`.
  Expected Qt/shiboken version is 6.11.1. Do not rebuild the binding from source.
- All real-app tests must isolate config/data as well as workspace/recovery.
  Do not override HOME or mutate the user's Pyzo preferences. Use fresh temporary
  directories and test-owned process cleanup. Qt execution/kernel sockets may
  require escalation; request it rather than hiding a permissions failure.
- Use meaningful state/failure assertions. Preserve historical acceptance notes;
  update obsolete expected behavior only with a link to its superseding rule.
  A passing model test does not establish equivalent live Qt behavior.
- For root tests, start with the touched unittest modules; broader coordinating
  discovery is `QT_QPA_PLATFORM=offscreen deps/pyzo/.venv/bin/python -m unittest
  discover -s spikes/peer_frames -p 'test_*.py'`. Nested tests include pytest-style
  functions; ensure pytest is available and run with `PYTHONPATH=deps/pyzo:.`.
  Record actual commands/results; do not treat collection failure as a skip.
- Completed task implementations may be committed using JJ, separately in each
  touched repository, after acceptance. Never absorb unrelated dirt. Record
  resulting commit IDs and any cross-repo dependency before handing back. No
  pushing or blanket `git add -A` fallback; investigate JJ/index discrepancies.
- Mark COMPLETE and link evidence only after all task criteria pass. The next
  task becomes eligible then; the original 019 gate required Astra acceptance of 018. The October
  review records the missing decision under the user's continuation authority. A blocker returns to Astra; it does not authorize a substitute feature.
- Do not move Experiment 014's Stage 4 to accepted. The batch completion returns
  to [Astra's self-handoff](../docs/handoffs/2026-09-06-local-retention-review.md).

## Evidence per task

Record the actual behavior and scope, state/failure cases exercised, exact test
commands and counts, isolated smoke logs, changed acceptance criteria, root/Pyzo
commit IDs, remaining issues, and the next eligible task. If an assumption is
falsified, explain it and retain the failing reproduction. Store larger notes in
`docs/evidence/task-NNN-local-retention.md` and link them from the task.
