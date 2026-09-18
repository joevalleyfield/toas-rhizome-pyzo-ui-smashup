# Task 021a progress evidence: explicit workspace runtime ownership

Date: 2026-09-18
Status: IN_PROGRESS

## Implemented checkpoint

Pyzo revision `30a01e5a` extracts `WorkspaceRuntime` in
`pyzo/core/workspaceRuntime.py`. The runtime owns the workspace identity,
backend, model, editor/shell host lookup tables, host serials, construction
cleanup, and exactly-once disposal. Existing `MainWindow` accessors remain
compatibility aliases while callers are migrated incrementally. Application
documents, commands, retention, and the coordinator remain outside the
runtime.

The factory closes a backend if model construction or callback binding fails;
runtime disposal clears only runtime-owned hosts and closes the backend once.
Application shutdown now disposes the runtime rather than bypassing it through
the backend alias.

## Passing checks

```text
PYTHONPATH=deps/pyzo ../../.codex-local/bin/uvt run --offline --python 3.12 \
  --with PySide6 --with <pinned QtAds wheel> --with ipython \
  pytest tests/test_workspace_runtime.py tests/test_application_controller.py \
  tests/test_peer_views.py tests/test_shell_groups.py -q
6 passed
```

The isolated real-Qt retained-buffer smoke reached `SECOND` after the
extraction. Its preceding editor, controller, debugger, tool, shell,
workspace-session, and pane-movement checks also passed in the bounded startup
matrix.

## Current blocker

The bounded startup matrix reaches the existing clean editor lifecycle check,
then fails while reconciling projected frame chrome after editor-host
recreation. The diagnostic assertion reports one stale status projection and
one newly live frame ID:

```text
status projected: {4876006784, 4876259584, 4947973184, 4948050816}
live frames:      {4876006784, 4876259584, 4948050816, 4947938752}
```

The same check also covers command projection. This is a real Qt lifecycle
gap, not a reason to loosen the assertion. The mismatch is structural rather
than a simple missing event drain: the runtime backend's authoritative
`frame_windows` set and the projectors' QtADS-discovered floating-window set
diverge during deferred frame destruction/creation. The next bounded
correction needs a projector reconciliation seam that accepts the owning
runtime's frame set, then the isolated startup matrix must be rerun. No
two-workspace routing or persistence work has begun.

The first failed smoke invocation loaded the user’s persisted Pyzo layout and
created four editor groups; subsequent runs redirected app-data, tools,
workspace, and recovery paths into test-owned directories. No user app-data
was changed by the acceptance runs.
