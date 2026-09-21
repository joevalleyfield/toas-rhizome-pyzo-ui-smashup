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
