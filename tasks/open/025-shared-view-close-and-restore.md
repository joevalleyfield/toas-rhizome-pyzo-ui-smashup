# 025: Correct shared-view close and failed-primary restore

## Status

COMPLETE — owner Codex; accepted 2026-10-04 after the full regression, live
retention matrix and application controls. Inserted during the expanded 023/024
integration gate; authorized by the user's continuation instruction.

## Reproductions and write surface

With all runtime focus routed, the seven historical live controls expose:
primary B construction failure aborting startup instead of isolating B;
close-A leaving an editor for retired `view-a` in the global manager; external
restart later accessing deleted editor hosts. Do not weaken the probes.

Allowed: root `lifecycle.py` and matching tests; Pyzo `main.py`,
`workspaceRuntime.py`, `applicationController.py` and focused tests; the live workspace probe, evidence and
roadmap documents. No new windowing system or expansion into Stage 4.

## State/assertion gate

Shared document close: one/many views, closing first/last registered view,
both close orders, distinct lifecycle objects, clean/dirty state, admission
failure/cancel, repeated close. Each retained view must detach its own widget
exactly once; non-final close cannot discard/save the resource; later final
close cannot call a destroyed earlier view. Assertions use distinct lifecycle
objects and counts, with unchanged document disposition and live view IDs.

Restore: preferred owner succeeds/fails; fallback owner succeeds/fails; no
loaded owners; all requested owners fail. Failed entries remain visible,
preserved and retryable; successful entries render normally. Native restore
focus cannot choose startup authority; retired/teardown events cannot select
deleted hosts. Assert actual loaded IDs, failed IDs and selected startup owner.

Each fix gets its own targeted verification cycle before the next fix. Full
live retention and peer/legacy smokes remain the final gate.

## Additional observed states

Queued text/cursor/content callbacks after unbind can reference retained shared
resources through a retired widget. Ignore them before reading that widget or
mutating the resource. The real two-workspace adapter assertion fails before
the guard and passes after it. Startup with modern open/closed/empty document
authority must not replay legacy disk paths; fresh migration still may.
Native editor/pane/frame close must address its owning runtime in A or B,
independently of foreground or compatibility aliases. The ownership matrix
failed the three B cases before correction; all six pass afterward.
These are retention integration corrections within the September contract.

## Completion evidence

Each closed retained view now detaches its own lifecycle; a remaining live
view becomes the final-close authority. Unbound editor callbacks cannot mutate
a shared resource or read retired view state. Startup isolates failed requested
owners, preserves their loaded-set request for retry, suppresses restore/teardown
focus, and skips legacy path replay when modern retained state is authoritative.
Editor, pane and frame close routes resolve their explicit runtime owner.

Before/after controls: lifecycle distinct-owner cases 2 failures then 45 tests
passing; preferred-runtime cases 4 failures then 5 tests/4 subtests passing;
retired-callback Qt control 1 failure then 2 tests passing; focus suppression
9 failures then 24 tests passing; modern startup 2 failures/1 pass then all
3 passing; close-owner matrix 3 failures/3 passes then all 6 passing. An initial
startup-test fixture import error was repaired before these product counts.

Final combined regression: 326 passed, 10 expected skips, 45 subtests (2.25s).
Nine live retention controls pass (27.01s); the secondary recovery probe also
checks native editor closure. Full peer and legacy controls pass; exact commands,
logs, dependency and commit ledger are in the
[023 integration evidence](../../docs/evidence/retention-integration-2026-10-04.md).
This closes the reproduced defects, without claiming every historical Qt timing
failure has one cause. Stage 4 execution remains separate.

## All-requested-owner failure checkpoint audit

The live extension to the original all-failed matrix exposed bootstrap fields
in durable publication: active owner and compatibility recovery were assigned
to a nonpersistent runtime. Assert the requested A/B set survives publication,
active identity is one of those requests, recovery keys are known persisted identities (including suspended C),
and no view is fabricated in bootstrap. Preserve pre-existing A/B records and
then retry both into real runtimes. The store validation rejects the incorrect
active/recovery fields before publication; no bad generation is committed.

The additional all-failed live control passes after preserving the requested set
and excluding bootstrap publication. It checks exact prior workspace/document
records before explicitly retrying both requested owners.

Accepted root lifecycle revision: `0448eee8`; additional all-failed probes:
root `7b9bed42`; required Pyzo runtime correction: `ed7cfb86`.
