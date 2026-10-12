# Windows menu lifecycle replay, 2026-10-11

Menu retirement now disconnects application/workspace subscriptions and removes
shell projections before workspace removal. Native Qt deletion and queued
callbacks are covered. Menu actions have explicit native parent ownership.
The selection probe uses the invoking frame's menu on Windows.

Final units: **708 passed, 41 skipped**, 2 warnings, 38.51s.
Final live: **21 passed, 5 failed**, 330.00s. The earlier full live report was
19 passed / 7 failed before the explicit action ownership repair.

Close, debugger, ordinary ingress, selection and scale (1/4/8 workspaces) pass.
Failures remain: application-smoke wait-run, automatic tool-state phase, and
peer, legacy and pristine-upstream restart parent exits. Raw diagnostics are
retained. Physical desktop acceptance is still open.

See [the worklog](../../../tasks/open/041-windows-support-replay.md) and
[the dependency patch](../../patches/windows-pyzo-support.patch).
