# Independent review of 022

Date: 2026-09-20 (America/New_York).
Reviewed root `2e9ab32d`, nested Pyzo `f377bfde`; both working copies were
clean before this review. This is a bounded review of 022's acceptance claim,
not completed architectural acceptance of every change in 015–022.

## Verdict

Keep 022 `REVIEW_REQUIRED`. The five delivered live tests pass independently,
but the statement that no control gaps remain is not supported. No production
failure was reproduced by the successful runs below. The findings concern
missing acceptance assertions and misleading measurement/evidence.

## Required corrections

1. **Measure actual durability completion under sustained edits.**
   `qt_live_document_roundtrip_probe.py:199–221` prints elapsed time when a
   fixed 1500 ms timer fires, after checking manifest mtime. It does not time
   the writer's completion. Its workload is a few tiny text replacements and
   reports one undo entry, not representative sustained editing or retained
   storage growth. Observe completion of the corresponding revision, report
   latency and history/storage size, and exercise continuing edits. This is
   explicitly required by 022's decisions and boundaries.
2. **Assert visible failure and refusal of destructive close while writes fail.**
   `qt_live_document_roundtrip_probe.py:157–172` checks coordinator FAILED,
   unchanged manifest mtime and unchanged source bytes, then repairs the writer
   before quitting. That proves the narrow source-write control, but cannot
   prove the reported failure was surfaced to the user or that failed retention
   prevents shell termination/view teardown. Keep the failure active through
   close, assert visible failure and surviving runtime/editor state, then test
   retry. Route any discovered product defect to its owning task.
3. **Assert document-owned external conflict handling.**
   `qt_live_document_roundtrip_probe.py:115–138` checks retained text, clean
   baseline and unchanged external bytes, then prints EXTERNAL CONFLICT without
   asserting conflict state, preservation of the observed external version,
   or explicit reconciliation. Those assertions could pass with conflict
   detection absent. Add the amendment's conflict assertions; keep the current
   no-overwrite assertions. The current test proves preservation on restore,
   not the whole external-conflict contract.
4. **Include the existing zero-open restart sequence in the persistent harness.**
   `test_local_retention_acceptance.py:132–137` runs first/retry/verify/cancel-close
   only. Add first/close/close-empty/reopen-empty with separate processes and
   expected markers. I ran that sequence independently and it passes, including
   the probe's shared-text and Undo/Redo assertions. This is missing regression
   coverage, not an observed product failure.

The evidence also needs exact reproducible smoke commands (the current example
uses a wheel placeholder), final revision/runtime references, retained logs,
skip explanations, and a populated handoff. I did not independently rerun the
vanilla or legacy smoke controls in this bounded review, and do not adopt their
reported passes as independent evidence.

## Independent validation

Live harness, exit 0:

```sh
RUN_LOCAL_RETENTION_ACCEPTANCE=1 PYTHONPATH=. ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest pytest spikes/peer_frames/test_local_retention_acceptance.py -q
```

Result: **5 passed in 15.13s**. The harness checks child exit status, required
markers, traceback output and teardown failure markers.

Combined root and nested collection, exit 0:

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest --with PySide6 --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q
```

Result: **281 passed, 6 skipped, 33 subtests passed in 3.38s**, two Qt
high-DPI deprecation warnings. This is a combined pytest invocation, not a
reproduction of Luna's two separate suite counts. Earlier attempts failed
because the fallback venv lacks pytest and because the combined invocation
initially omitted Pyzo's bundled yoton path; neither was counted as a skip.
The wrapper required sandbox escalation to access its configured local cache.

Additional zero-open-workspace control, exit 0:

```sh
PYTHONPATH=. ./.codex-local/bin/uvt run --offline --python 3.12 python - <<'PY'
import tempfile
from pathlib import Path
from spikes.peer_frames.test_local_retention_acceptance import run_owned_probe
with tempfile.TemporaryDirectory(prefix='pyzo-022-review-zero-') as directory:
    for phase, marker in [('first', 'FIRST WORKSPACES workspace-a workspace-b'), ('close', 'CLOSE WORKSPACES workspace-b'), ('close-empty', 'CLOSE WORKSPACES'), ('reopen-empty', 'REOPEN WORKSPACES workspace-a')]:
        elapsed, output = run_owned_probe(phase, Path(directory))
        assert marker in output, output
        print(phase, f'{elapsed:.3f}s', 'PASS', flush=True)
PY
```

All phases passed: first 0.733s, close 0.803s, close-empty 0.804s,
reopen-empty 0.717s. Temporary application data and separate test-owned process
groups were used by the existing runner. These timings are process durations,
not checkpoint latency.

No implementation changes or commits were made during this review. Stage 4
and overall retention-batch acceptance remain unchanged.

## Correction follow-up

The bounded corrections were applied after this review. The persistent harness
now covers sustained completion, active failure through close refusal and
retry, explicit recovery conflict metadata, and the zero-open restart
sequence. The tightened harness passes seven tests; the combined root/Pyzo
suite passes 281 tests with 8 skips. The task remains `REVIEW_REQUIRED` for
acceptance of the updated evidence.

## Independent second review — 2026-09-21

Reviewed root `59f94bf3` and Pyzo `0c5c3f20`. Both working copies were clean
before review. Verdict: **retain REVIEW_REQUIRED**. Two of the four findings
are addressed; external-conflict coverage and measurement remain incomplete.

### Accepted corrections

- The persistent harness now runs first/close/close-empty/reopen-empty in
  separate processes and retains the shared-text and Undo/Redo assertions.
- The checkpoint failure remains injected through application close. The
  production writer surfaces a status message; the test observes cancellation,
  surviving editor/workspace state, then successful coordinator retry.
  Pyzo's four-line change adds failure messages in the writer and exit logger.

### Remaining findings

1. **High: the external-conflict test seeds a different recovery path.**
   `qt_live_document_roundtrip_probe.py:98–104` manually calls
   `_retainPeerDocuments` to create a compatibility recovery snapshot. The
   second phase now expects two editors with the same filename and identical
   retained text: one ordinary restored editor without the conflict flag and
   one recovery editor with it. This does not establish document-owned conflict
   detection for ordinary automatic retention, preservation of the observed
   external contents in retained state, or explicit shared reconciliation.

   I independently repeated the two-process external-change scenario using a
   temporary copy of the probe, removing only that manual seeding block from
   the first phase. The second phase printed the restored editors' text and
   `_peerRecoveryConflict` flags, then performed normal lifecycle shutdown.
   Both processes exited 0 through `run_owned_probe`, with output:

   ```text
   EXTERNAL DURABLE
   UNSEEDED EXTERNAL [('retained\n', False)]
   DISK external
   ```

   Thus ordinary retention preserves the working text and external source
   bytes, but does not produce the conflict marker that the new test asserts
   for its manually seeded recovery lineage. This reproduces a path-specific
   conflict-detection gap, not source data loss. The only production flag
   assignment found is in `_restorePeerRecoverySession`; its `external_text`
   is a local variable and is replaced in the editor with snapshot text.

   Required correction: exercise the ordinary automatic retention/restart
   path without injecting a compatibility snapshot. Route any necessary
   production correction to the document retention adapter owner (019, with
   016 if persisted conflict representation changes). Assert document-owned
   conflict state, retained observed external contents, visible choice and
   reconciliation shared by views; keep legacy recovery as a separate control.

2. **Medium: the new metrics still do not measure the required workload.**
   `qt_live_document_roundtrip_probe.py:265–278` starts timing only after all
   24 edits and an additional 80 ms timer interval. It polls durable revision
   every 25 ms. The reported 0.107s is therefore a residual wait after the
   workload, not a measured maximum edit-to-durability interval during it.
   There is no assertion that a checkpoint completed while editing continued.
   `STORAGE_BYTES` measures only `manifest.json`; document text and Undo/Redo
   are stored in `generations/.../resources-*.json`, so their size is excluded.
   The workload coalesces to one history entry and does not assess history
   growth. The wrapper checks metric labels without numerical limits.

   Required correction: timestamp edit revisions and their writer completions,
   report maximum edit-to-durable latency and writes during ongoing edits,
   enforce the chosen persistence bound, and measure actual resource/history
   payload plus retained generations for a workload with multiple undo groups.
   The new revision polling is useful progress, but does not close finding 1
   from the original review.

### Independent validation at the new revisions

The same live-harness command documented above returned exit 0:
**7 passed in 20.68s**.

The same combined-suite command above, with `-rs` added, returned exit 0:
**281 passed, 8 skipped, 33 subtests passed in 2.34s**, two Qt high-DPI
deprecation warnings. Seven skips are the opt-in live harness (run separately);
one is `test_qtads_backend.py:124`, because the fork implements all four tab
sides. Vanilla/legacy smoke was not independently rerun in this review.

The diagnostic used `PYTHONPATH=. ./.codex-local/bin/uvt run --offline --python
3.12 python` to create a temporary modified probe and call `run_owned_probe`
for `external-first` and `external-second`, using the existing phase/directory
environment names and `PYZO_TEST_WORKSPACE_PERSISTENCE=1`. Between processes,
it wrote `external\n` to the test-owned `saved.py`. It removed the first phase's
block from `document_id = ...identity(editor)` through `_retainPeerDocuments`,
and replaced the second callback's assertions with the diagnostic output above
and normal shutdown. No production files were modified for this reproduction.

Overall retention-batch and Stage 4 acceptance remain unchanged. Review changes
are documentation only, uncommitted.

### Correction follow-up — 2026-09-21

The two bounded corrections from this review are now implemented. The ordinary
external-change phase no longer seeds compatibility recovery; the restored
document is compared with its persisted clean baseline, and the shared
resource/editor receive the current external text and signature plus a visible
warning. The sustained workload now timestamps each coordinator revision and
writer completion, forces multiple undo groups, verifies writes during editing,
and sums all files below the workspace persistence root.

Verification after the correction:

```text
7 live tests passed in 20.01s
281 passed, 8 skipped, 33 subtests passed in 2.33s
2 targeted correction tests passed in 5.23s
```

The remaining review findings are closed by evidence; 022 remains
`REVIEW_REQUIRED` pending the acceptance decision.

### Third-review correction follow-up — 2026-09-22

The third-review corrections are implemented. Conflict text, signature,
encoding, and conflict state are now part of the document-resource persistence
record and survive registry serialization. External source reads use Python's
source-encoding detection, with an unavailable external version represented
without raising a decode exception; the live control now exercises a Latin-1
encoded source file and verifies that its bytes remain unchanged.

The sustained workload no longer calls document or coordinator flush. It runs
long enough for automatic scheduling to fire, records writer completion against
the earliest edit in each coalesced revision batch, and requires a write during
editing plus at least one coalesced batch.

Verification after the third-review correction:

```text
7 live tests passed in 20.30s
281 passed, 8 skipped, 33 subtests passed in 2.26s
2 targeted correction tests passed in 6.23s
```

022 remains `REVIEW_REQUIRED` pending Astra's acceptance decision.

## Independent third review — 2026-09-22

Reviewed root `8da4d712e88e8e6209d192da696a5500cccde3a6` and Pyzo
`a48eca2d7f5f4e51bef1d469773655634765fd53`. Both working copies were clean
before this review. **Keep REVIEW_REQUIRED**; the preceding implementer claim
that the remaining findings are closed is not accepted.

Accepted progress: ordinary UTF-8 retained restore now detects divergence
without legacy recovery seeding and displays a warning. The storage metric
includes the whole workspace persistence tree and the harness requires more
than one history entry. Previously accepted failure/retry and zero-open
coverage remain accepted.

### Findings requiring correction

1. **High: observed external state is still not durable or reconciled.**
   The three fields added to `DocumentResource` are absent from
   `DocumentResourceRegistry.persistence_snapshot` and
   `restore_persistence_snapshot` (`document_resources.py:620` onward).
   A direct registry roundtrip after setting conflict=true, external text and
   signature produces `False, None, None`. Restore rereads the current source,
   so a later external change replaces the previously observed version rather
   than retaining it for reconciliation. Searches for the three fields found
   initialization, detection and editor copies, but no resolution path or
   shared-view update after resolution. The live test verifies only first
   detection. Persist the observed version/conflict state and implement/test
   explicit document-owned reconciliation across views and restart. This is
   the outstanding external-conflict requirement from the prior reviews.

2. **High: the new detector fails on supported non-UTF-8 files.**
   `main.py:2836` opens every source as UTF-8 and catches only `OSError`.
   `UnicodeDecodeError` escapes. Pyzo's existing `_loadTextFromFile` honors BOMs
   and PEP 263 encodings, so a valid Latin-1 Python file is affected. I executed
   the exact `_markPeerExternalConflict` method extracted by AST against a
   temporary file containing `# coding: latin-1\n# caf\xe9\n` with its matching
   decoded clean baseline; it raised `UnicodeDecodeError`. This is a focused
   method reproduction, not a full application startup run. The method is
   called unguarded in retained-editor restoration. Reuse compatible decoding
   and normalization and preserve undecodable bytes without aborting restore;
   add unchanged/changed encoding controls. This regression is introduced by
   the new production correction and belongs with its owner.

3. **Medium: sustained metrics bypass automatic retention.**
   `qt_live_document_roundtrip_probe.py:321–322` calls both document flush and
   coordinator flush after every three insertions. These force synchronous
   writes regardless of the scheduler; the workload completes in roughly one
   second. Thus writes-during-edit and the latency bound can pass even if
   automatic scheduling never fires. The latency comprehension at lines
   275–278 also includes only revisions whose exact number completed, omitting
   earlier edits coalesced into those snapshots. Remove forced durability
   flushes during the measured workload, run across multiple automatic
   intervals, and map every edit to the first successful durable revision
   covering it. Undo-group boundaries should not force persistence. Prove a
   disabled/delayed scheduler fails the timing control. Full storage counting
   and numerical assertions should be retained.

### Independent results

Using the previously documented commands at these revisions:

- Live harness: **7 passed in 20.26s**, exit 0.
- Combined root/Pyzo suite with `-rs`: **281 passed, 8 skipped, 33 subtests
  passed in 2.47s**, exit 0; two existing Qt high-DPI deprecation warnings.
  Seven skips are the separately run live harness; one is the four-tab-side
  fork control at `test_qtads_backend.py:124`.
- Focused diagnostics using `deps/pyzo/.venv/bin/python`: exact detector method
  raises on the Latin-1 fixture; actual registry persistence roundtrip loses
  the external conflict/text/signature fields. Fixtures were temporary and
  no production source was changed.

Vanilla/legacy smoke was not independently rerun. No implementation changes
or commits were made. The review and handoff updates are documentation only.
Overall batch and Stage 4 acceptance remain unchanged.

## Independent fourth review — 2026-09-22

Reviewed root `b7849976` / Pyzo `86f6c70a`; both working copies were clean
before review. **Keep REVIEW_REQUIRED for one remaining conflict-lifecycle
blocker.** Encoding and automatic-scheduling corrections from the third review
are accepted for this bounded acceptance slice.

Independent results using the same commands documented above:

- Live matrix: **7 passed in 20.59s**, exit 0.
- Combined root/Pyzo: **281 passed, 8 skipped, 33 subtests passed in 2.39s**,
  exit 0; two existing Qt deprecation warnings.
- Exact detector method with a Latin-1 Python fixture: successful decoding.
- Actual resource snapshot/restore: all populated conflict fields survive.
- Negative scheduling control: a temporary probe copy replaced
  `coordinator.run_due` with a no-op before measured edits. The latency phase
  failed at a six-second external deadline without its completion marker;
  the runner terminated its owned process group. No production source changed.

The workload no longer forces durability flushes, includes coalesced edits in
its maximum latency, and counts the persistence tree. These changes address
the prior scheduling/measurement finding; this is not a production performance
or exhaustive workload claim.

### Remaining high-priority finding: restore discards unresolved conflict state

`MainWindow._markPeerExternalConflict` (`main.py:2827` onward) still resets all
four external fields, then replaces them with the current disk observation.
It does not consult the persisted external fields in `record`. The method is
called for each restored editor after resource deserialization. Consequently,
the newly added serialization alone does not preserve the observed version
through the complete restore path.

Focused reproduction using the actual registry and exact detector method
extracted from the reviewed source with AST (not a full application run):

1. Create a retained document with clean baseline `baseline\n`.
2. Write Latin-1 external contents `# coding: latin-1\n# café\n` and detect the
   conflict. Snapshot and restore the registry; verify those external contents
   survive this serialization step.
3. Change the source back to `baseline\n` without resolving the conflict.
4. Invoke the restore detector with the restored resource and saved record.

Observed output:

```text
Latin-1 decode and registry roundtrip: PASS
After restore detector: 'baseline\n' conflict= False
Unresolved observed external version lost without reconciliation: REPRODUCED
```

A different new disk version similarly replaces the earlier observation.
Search of all four fields still finds initialization, serialization,
deserialization, detector assignments and editor copies, but no explicit
document-owned reconciliation operation. This is the same unresolved
conflict-lifecycle requirement from the earlier reviews, not a new scope item.

Required bounded correction: retain an unresolved observed version when disk
changes again; represent the new observation without silently overwriting the
old one; resolve only through an explicit document-owned operation and update
all views. Add a three-process test (detect, persist, change disk, restart)
covering both another external version and a return to baseline, plus shared
resolution assertions. Keep the existing no-source-overwrite checks. This
belongs to the document-retention adapter/persistence owner, with 022 supplying
the acceptance control.

No implementation changes or commits were made. Review/handoff changes are
documentation only. Batch/Stage 4 acceptance remains unchanged; vanilla and
legacy smoke were not independently rerun in this review.

### Fourth-review correction follow-up — 2026-09-23

The unresolved-observation lifecycle is now implemented. The first observed
external version remains authoritative while later disk signatures are stored
as separate latest observations. Both survive persistence and restart. The
document-resource adapter now exposes explicit external resolution, clears the
unresolved fields only through that operation, and projects resolved text to
every bound view, including the initiating editor.

Verification:

```text
7 live tests passed in 21.93s
282 passed, 8 skipped, 33 subtests passed in 2.49s
1 focused live lifecycle test passed in 3.96s
1 focused registry-resolution test passed
```

022 remains `REVIEW_REQUIRED` pending Astra's final acceptance.

## Independent fifth review — 2026-09-23

Reviewed root `ec6fdf0e` / Pyzo `41300856`; both working copies were clean
before review. **Keep REVIEW_REQUIRED for resolution durability.** The original
unresolved observation now survives the three-process return-to-baseline case,
with the later observation stored separately. Explicit resolution clears the
live conflict state and warning. These parts of the prior finding are accepted.

### High-priority finding: resolution does not schedule retention

`DocumentCollectionAccess.resolve_external` in
`deps/pyzo/pyzo/core/applicationController.py:380–403` updates the registry and
projects the result but never calls `_on_edit`. Other mutating operations,
including undo and redo, call this callback, which is wired to
`_peerRetentionCoordinator.edit()`. Changing the resource revision alone does
not capture or schedule a checkpoint.

I ran a temporary variant of the existing three-process external probe using
the same isolated `run_owned_probe` helper. The first two phases were unchanged.
Before the third process I restored disk contents to `disk\n`. In the third
callback I resolved the conflict with the existing API, recorded coordinator
revision and dock warning, then waited 1800 ms and loaded the actual durable
record through `WorkspacePersistenceStore` before normal shutdown:

```text
RESOLUTION REVISION 1 1
WARNING AFTER RESOLUTION False
DURABLE CONFLICT AFTER WAIT True
```

Thus the visible resolution is not retained automatically even after the
normal one-second checkpoint interval. A crash can restore the unresolved
state; resolved text changes can also remain outside the captured snapshot.
The current live callback checks only memory and immediately quits, allowing
the shutdown checkpoint to hide this gap. The registry test checks snapshot
roundtrip before resolution, not automatic durability after it.

Required bounded correction: finish the resolution transaction and notify the
retention coordinator so it captures resolved text, history/baseline and cleared
observations. Extend the live control to wait for that resolution revision's
automatic durable completion, terminate without orderly shutdown, and restart
to verify resolved text and cleared conflict state. Preserve the no-source-write
assertion and shared-view behavior. Keep this with the document adapter owner;
022 supplies the regression control.

### Independent verification

Using the previously documented live and combined-suite commands:

- **7 live tests passed in 22.17s**, exit 0.
- **282 passed, 8 skipped, 33 subtests passed in 2.31s**, exit 0; two existing
  Qt high-DPI deprecation warnings.
- The temporary three-process durability diagnostic above exited 0 after
  reporting the stale durable conflict; normal lifecycle cleanup followed.

No production source was modified by the diagnostic. Review changes are
documentation only and uncommitted. Vanilla/legacy smoke was not independently
rerun. Overall batch and Stage 4 acceptance remain unchanged.

### Fifth-review correction follow-up — 2026-09-23

External resolution now invokes the application adapter's existing retention
edit callback after updating the shared resource and projecting all views. The
live control waits for the resolution revision to become durable, terminates
the test-owned process without orderly shutdown, and restarts to verify the
resolved text and cleared conflict state are recovered.

Verification:

```text
7 live tests passed in 24.13s
282 passed, 8 skipped, 33 subtests passed in 2.33s
1 focused resolution durability test passed in 6.07s
```

022 remains `REVIEW_REQUIRED` pending Astra's final acceptance.
