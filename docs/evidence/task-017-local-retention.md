# Task 017 local retention evidence

Date: 2026-09-07

## Delivered boundary

Added `RetentionCoordinator`, a technology-neutral checkpoint scheduler with
injected clock, scheduler, owner-thread capture callback, and asynchronous
writer callback. It provides explicit durable, pending, writing, and failed
states and a flush barrier.

- The first edit schedules a checkpoint one second later by default.
- Sustained edits replace the pending immutable snapshot without moving the
  first-edit deadline.
- Only one writer can be in flight; edits during a write remain pending.
- Successful completion advances durable revision only for the matching write.
- Failures retain the snapshot and error for visible retry.
- Stale completions are rejected and cannot clear newer pending state.
- Unchanged state and idle flushes do not create redundant writes.
- No Qt or source-file integration was added.

## State assertions

- Fake-clock deadline test proves sustained edits reach the original due time.
- Writer-call count proves coalescing and single-writer behavior.
- In-flight edit test proves newer revision remains pending after older success.
- Failure test proves error visibility and retry publication.
- Stale completion test proves durable revision is not advanced by an unknown
  generation.

## Verification

- Coordinator suite: **9 tests, OK**.
- Combined retention/persistence/recovery/document/lifecycle subset: **106
  tests, OK**.
- Python 3.12 compilation: **passed**.
- `git diff --check`: **passed**.

## Scope and handback

Changed only the allowed new coordinator/test files, package exports, task
status, and evidence. Task 018 is now dependency-eligible; its real-editor
undo proof remains intentionally separate.

## Correction pass

Timer callbacks that fire during an in-flight write now clear their stale
scheduled flag so completion reschedules pending work. Each write has a unique
attempt identity in addition to its document revision; a late callback from a
failed attempt cannot complete a retry with the same revision.
