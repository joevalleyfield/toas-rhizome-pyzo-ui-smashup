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
