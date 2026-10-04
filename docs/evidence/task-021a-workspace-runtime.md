# Task 021a progress evidence: explicit workspace runtime ownership

Current decision, 2026-10-04: COMPLETE at the reviewed runtime plus Pyzo
focus correction `e7274793`. See [current review](retention-integration-2026-10-04.md).
The checkpoint/blocker account below is historical; its missing final task
decision is now reconciled with current ownership tests and full peer smoke.

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

The bounded startup matrix now reaches the pane-movement and clean editor
lifecycle checks. The chrome reconciliation seam is implemented, but the
matrix still does not complete deterministically: recent runs alternate
between the existing editor-list identity assertion during pane movement and
the projected/live frame equality assertion during cleanup.

The earlier diagnostic assertion reported one stale status projection and one
newly live frame ID:

```text
status projected: {4876006784, 4876259584, 4947973184, 4948050816}
live frames:      {4876006784, 4876259584, 4948050816, 4947938752}
```

The same check also covers command projection. This remains a real Qt
lifecycle gap, not a reason to loosen the assertion. The bounded correction
now passes the owning runtime's frame set explicitly and performs actual
chrome cleanup; the remaining work is to reconcile the full startup matrix.
No two-workspace routing or persistence work has begun.

The first failed smoke invocation loaded the user’s persisted Pyzo layout and
created four editor groups; subsequent runs redirected app-data, tools,
workspace, and recovery paths into test-owned directories. No user app-data
was changed by the acceptance runs.
