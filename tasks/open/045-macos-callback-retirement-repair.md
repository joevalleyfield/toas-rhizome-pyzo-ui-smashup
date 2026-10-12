# macOS callback retirement repair

## Status

Claimed by Engineer, 2026-10-12. Compiled as Project Manager from Journal objective repair-macos-callback-retirement.

## Objective

Implement the two explicitly approved callback lifetime fixes, one verified cycle at a time.

## Acceptance Criteria

- Pre-edit state gate and user confirmation: completed under task 044.
- Focused regression tests fail before each repair and pass afterward.
- Checkpoints suspend during exit and resume after canceled/preflight-failed exits; queued callbacks and reentrant transitions remain safe.
- Broker events retire before shell release; queued/native-deleted callbacks no-op while normal live disconnects, foreign/reconnect checks and error visibility remain.
- Preserve original controls/deadlines; run local and actual hosted verification and retain all results.
- Publish draft dependency PR and update integration PR #3 with exact source pin; no merges or Windows-specific edits.

## Allowed Write Surfaces

Isolated pyzo-review source/tests and fork branch, integration manifest/gitlink if tracked, required context-consumer review, task 045, docs/evidence and draft PR metadata. Windows-specific fixes and original acceptance thresholds/deadlines are excluded.

## Required Completion Evidence

Before/after regression outcomes, exact dependency/integration commits, focused/full/local/hosted results, PR links and validation limits.
