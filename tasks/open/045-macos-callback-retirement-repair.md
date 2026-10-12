# macOS callback retirement repair

## Status

Completed by Engineer, 2026-10-12. Compiled as Project Manager from Journal objective repair-macos-callback-retirement.

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

## Completion Evidence

- [Repair evidence](../../docs/evidence/macos-callback-repair-2026-10-12/README.md), pre-edit state gate under task 044, explicit user answer "Proceed with both fixes".
- Pyzo 6d6b8b6c789f12b33f8afb4276f99e25fbd8bd79, draft https://github.com/joevalleyfield/pyzo/pull/3. Checkpoint and shell regressions fail before repairs; 79 focused controls pass afterward. One repair verified before the next.
- Integration 822139b046de0be2b54be01323fe4477aa0b2b62 pins that exact source and reconciles required 724-reference audit without changing classifications or original controls/deadlines.
- Local fresh source replay, cached working runtime: six bootstrap passes/one skip, 782 unit passes/30 skips/two warnings, all 27 live controls pass in 156.16s. Strict local observed close/debugger also pass.
- Actual hosted timing run 38321395657/job 115050064395 at integration 79bc5933: six original close/debugger tests plus two observed probes pass on three virtual M1 CPUs/7 GiB, with no exception markers; all 28 queries succeed.
- Actual full canonical run 38321657867/job 115051151543 at audited integration 822139b0: fresh build and macOS acceptance succeed, six bootstrap/782 unit/27 live passes. Live controls take 270.14s. XML/setup/job logs retained and independently parsed.
- Overall workflow remains failed: Linux Run Cell assertion after nine live passes; Windows affinity-seed smoke deadline after eleven live passes. Evidence retained; no platform-specific repairs or merge in this task.
- Draft integration https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/pull/3; Stage 7/task 041 remain open. Historic PID timeout was not reproduced or repaired.
- Skipped: visible desktop acceptance, hardware emulation/stress, and new local runtime build (existing cached runtime reused because generated-runtime hidden plugin flags remain unexplained). Actual hosted builds were fresh.
- Notes Keeper independently re-verifies committed source, manifests, XML and observed logs after completion before compiling Journal knowledge.
