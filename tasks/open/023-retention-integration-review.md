# 023: Reconcile retention integration and unblock the current roadmap

## Status

REVIEW_REQUIRED — owner Codex; reviewed 2026-10-04. Focus correction accepted
at Pyzo `e7274793`; current 018 and 021a decisions are closed. The remaining
migration selection gate is assigned to 024. See
[evidence](../../docs/evidence/retention-integration-2026-10-04.md).
Starting root parent `d50c07af`, Pyzo parent `776cf29c`. The initial
read-only JJ snapshot appeared clean, but normal snapshotting later revealed
existing uncommitted September review documents; these were preserved and
committed separately as roadmap cleanup at root `b0705f64`.
Authorized by the user's request to continue next steps and roadmap cleanup,
preserving the September amendment.

## Outcome and allowed writes

Independently review the retention batch and unresolved 018/021a gates; update
the roadmap from observed evidence. Root task/plan/evidence documents and
isolated smoke helpers are allowed. A reproduced full peer-smoke failure
authorizes a bounded correction to Pyzo's focus handlers in `core/main.py`
and focused `tests/test_peer_focus.py`. No execution migration belongs here.

## Pre-edit state and assertion gate

Focus input is either absent, unknown/retired, or owned by a loaded runtime.
Owned input is an editor, shell, or tool dock in either the primary or a
secondary runtime. Repeated events must be idempotent; sequential events must
follow the last valid owner. A widget event is on the content/descendant of
one such dock, or outside all registered contents. Legacy mode retains its
existing editor/shell host route. Execution affinity must remain unchanged.

Machine assertions in `test_peer_focus.py` cover this cross product:
`activations == [(owner, pane)]` for each valid event;
`active_editor is expected_editor`; `active_shell is expected_shell`;
`execution_shell is original_execution_shell`; no activation/selection for
absent/retired inputs; descendant focus calls only the owning backend.

Current gap: `_onFocusedDockWidgetChanged` returns before selecting shell hosts
in peer mode. `_activatePeerPaneForWidget` scans only the primary backend.
Existing full peer smoke fails at `main.py:4160`, asserting the newly focused
first shell is current. This is a deterministic ownership gap; no timing
delay or weakened smoke assertion is authorized.

## Acceptance

- Focus state matrix passes and full isolated peer smoke completes, including
  Run/live debug, postmortem, multi-kernel affinity, and zero-frame recreation.
- Legacy non-peer control passes with fresh temporary application data.
- 018 real-widget history and 021a ownership/failure/cleanup evidence receive
  current decisions; do not infer historical Astra approval.
- Re-run combined root/Pyzo and live retention controls. Preserve deferred
  native OS interaction/platform validation and later execution/tool gates.
- Record exact commands, runtime/dependency revisions, logs, remaining limits,
  and separate accepted commits before advancing NEXT.
