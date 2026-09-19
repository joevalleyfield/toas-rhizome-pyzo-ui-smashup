# Task 021a1 progress evidence: bounded runtime teardown

Date: 2026-09-18
Status: IN_PROGRESS

## Completed correction

Pyzo’s run-cursor timer is now parented to its editor, single-shot, and
connected to a normal method. Destroying an editor therefore destroys the
timer with its owner instead of leaving a lambda callback that later invokes a
deleted Qt object.

## Verification

The configured `uvt` real-Qt startup smoke passed all existing functional
markers and produced no callback traceback:

```text
Pyzo real-pane movement matrix smoke test passed
Pyzo clean editor lifecycle matrix smoke test passed
Pyzo dirty editor lifecycle matrix smoke test passed
Pyzo independent shell-dock smoke test passed
Pyzo zero-frame survival and default recreation smoke test passed
Pyzo ordinary run and live-debug smoke test passed
Pyzo post-mortem re-entry smoke test passed
Pyzo multi-kernel execution-affinity smoke test passed
Stopped our command server.
```

The focused harness tests pass:

```text
20 passed, 3 subtests passed
```

The injected-abort run returned exit code `1`, stopped the test-owned command
server, and emitted no delayed Qt callback traceback. The external harness
unit test also verified that a sleeping owned process is terminated at its
deadline with exit code `124`.

## Remaining scope

The external deadline, test-abort cleanup entry point, process-tree cleanup,
and explicit proof that forced termination is reported as failure remain. The
editor timer fix does not replace those requirements.
