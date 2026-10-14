# Stage 7 branch integration — 2026-10-13

The coordinator combines the Stage 7 branch, macOS callback-retirement branch,
and scoped stale-reply correction. Pyzo is pinned to
`25937341b1cff833a2e7539b0caf4a48e2bd8e11`, which contains both
`803afaf3` and `6d6b8b6c` in its ancestry. The binding/native QtADS pins and
acceptance assertions/deadlines are preserved. Existing experiment paths and
historical evidence remain intact, including the independently named task 042
artifacts from parallel work.

## Reconciliation and state coverage

The checkpoint conflict uses the macOS capture/preference ownership rechecks
and exit timer suspension/resume. Stage 7's affiliation exit guard, pending
smoke evaluation, cwd/DPI changes and find-timer retirement remain. The shell
conflict uses early broker identity retirement, subscription unbinding and
native-validity checks; the Stage 7 close-order regression keeps its original
assertions with a broker subscription fixture matching the real interface.

Pre-edit coverage includes loaded/missing context, closing/exiting owners,
owner removal and callbacks during capture/preferences, active/inactive/missing
timers, cancellation/preflight/cleanup/replacement failures and reentrant exit,
current/foreign/missing broker identities and native deletion. Existing effects
tests assert, among others:

```python
assert main._peerContextSnapshot is None
assert main._peerApplicationExitRequested is (not resumed)
assert timer.isActive() is (active and resumed)
assert shell._brokerConnection is None
assert not broker.closed._handlers
assert calls == before
```

All 724 contextual reference identities, classifications and proof assignments
are preserved. Reviewed scope hashes/line positions change in the checkpoint,
shell module and committed-close scopes; the macOS lifetime proof statements
and effect tests are retained in the audit.

The macOS query observer now wraps both `result` and `result_or_cancel` and
recognizes calls routed through the pending-aware poller. It forwards original
arguments, values (including False/None), pending/errors and exceptions. Only
queries owned by the observed probe are logged. Forwarding/ownership tests and
strict real close/debugger observation verify the integrated interface.

## Validation and landing gate

- 118 focused dependency lifecycle/readiness tests pass; one Windows-only
  control skips on the local Mac.
- 15 integration-specific observer, ownership-audit and held-request tests pass.
- Full local canonical acceptance: **806 passed, 32 skipped, two Qt deprecation
  warnings**; **all 27 live controls passed in 160.12 seconds**.
- Strict observed close/debugger probes both pass under their original 35-second
  deadlines, emit pending-aware query records and contain no forbidden traceback,
  uncaught-event or teardown markers.

[Raw local logs/XML](stage7-integration-2026-10-13/) retain the results. Local
validation uses the matching existing Qt/PySide6 6.11.1 and dev10 binding runtime
through an isolated Python 3.12.13 environment, with pinned pytest 8.3.5,
pytest-subtests 0.14.1 and psutil 7.2.2. Copied QPA plugin files avoid the existing
runtime's hidden-file flags without modifying that runtime. This local replay
is not a fresh native build or desktop interaction acceptance.

[Dependency integration PR](https://github.com/joevalleyfield/pyzo/pull/4)
and the coordinator integration PR carry the exact tested revisions and canonical
hosted run links. Landing requires fresh Windows/Linux/macOS build, bootstrap,
units and live acceptance on the combined coordinator revision. The dependency
lands before the coordinator so the pinned source remains published and reachable.

Stage 7 stays open for native Linux desktop validation and the remaining full
requirement/platform matrix. File Move/Fork UX, live shell migration, zombies,
portable synchronization and broad TOAS/Rhizome integration remain deferred.
