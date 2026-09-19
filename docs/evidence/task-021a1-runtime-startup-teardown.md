# Task 021a1 completion evidence: bounded runtime teardown

Date: 2026-09-18
Status: COMPLETE

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

The full real-Qt smoke also completed through the external harness with exit
code `0`, all peer-frame markers, and `Stopped our command server.`

After that first run exposed a reentrant test-timer race, the callback runner
was guarded so the periodic live-debug tick defers while a UI callback is
processing. Two independent fresh-process reruns then completed the full
matrix with exit code `0`, explicit completion markers, no callback traceback,
and clean command-server shutdown. The focused Pyzo runtime/controller/view
tests passed `5 passed`; the root harness tests passed `2 passed`, including a
descendant-process cleanup assertion.

The external harness also remains separately failure-signaling: a forced
deadline returns `124` and emits `EXTERNAL_DEADLINE_FAILURE`, while callback
injection exits nonzero and uses test-only cleanup without Save/Discard or
shell-termination dialogs.

## Remaining scope

No 021a1 acceptance scope remains. The next slice is 021b live workspace
routing; production suspend/resume remains in 021.
