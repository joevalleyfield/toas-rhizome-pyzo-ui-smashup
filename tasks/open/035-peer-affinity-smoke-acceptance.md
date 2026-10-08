# Stage 7: Peer affinity smoke acceptance

## Status

CLAIMED by Codex, 2026-10-08. User granted carte blanche to reproduce and repair
the affinity timeout/reporting, then execute Stage 7 scale and final census gates.
Dependencies: accepted 034. This bounded slice changes smoke behavior only unless
read-only evidence demonstrates a production routing defect.

Allowed: Pyzo startup/smoke helpers and tests; root process-owned probes/harness;
task/evidence/checklist links. Preserve live eligibility/provenance refusal,
existing deadlines, kernel routing and September deferrals.

## Pre-edit states, assertions and coverage

| State | Assertion | Handling/gap to inspect |
| --- | --- | --- |
| Version absent/present × connected/disconnected × Starting/Ready/More/Busy/Debug/Dead | `seed_sends == []` until both live shells are Ready; eligible receipt required | smoke checks version only; runtime sync_shell checks connection/version/state |
| One ready shell, second startup receipt before Ready | no early seed; exactly one send per shell after readiness | suspected early refusal, diagnose native resolution |
| Ready changes after gate; reconnect/generation change | failure/refusal remains bounded, no foreign/untagged fallback | production service guards; do not relax |
| Seed in flight / received / errored / cancelled | exact identities and cwd before affinity actions; no repeat mutation on retries | current wait-affinity-seed polling |
| Focus drift; independent native contexts | chosen execution target unchanged by focus; exact first/second receipts | existing affinity assertions to replay |
| Smoke success / exception / timeout / callback failure | success exit 0+completion; all failures nonzero and no completion marker | qApp exit ignored by start except _test_exit_code |
| Failure before/after kernels launch; pending timer; teardown failure | test-owned process group ends, cleanup error cannot become success | existing abort callback cleanup/external deadline |
| Peer/legacy normal startup | actual host type and all existing control markers | legacy test timer remains compatible |

No source repair before diagnostic observation. Authorization covers the bounded
repairs; no strict external-validation mode. Test live phase transitions and
forced timeout/exception exits, then full suites and serial peer/legacy smokes.

## Diagnostic and first repair cycle

Actual trace: first shell `3.12/Ready/connected` resolves; second
`3.12/empty-state/connected` returns `NO_TARGET`. Only version arrives before
startup completes; existing refusal is correct. The timeout calls qApp.exit(1)
but start ignores its return and only checks `_test_exit_code`; process returns
success and emits the completion marker.

Refine readiness assertion to both shell versions, Ready states and positive
connection counts before sending once. Route timer exception/timeout through
the existing `abort_test_run`, which stops timers, aborts callbacks, cleans test
kernels/server, sets `_test_exit_code=1` and exits. Add injected held-phase and
exception modes to the test-owned smoke probe, never normal startup. Assert
failure exits 1 and lacks APPLICATION SMOKE COMPLETE. Replay further affinity
assertions against the accepted current execution contract before changing any.

The first replay correctly exits 1 but reaches the same early-startup refusal in
`wait-run`: the initial shell gate also checks version only. Extend the readiness
state/assertion to the initial file-run phase before repair; all three startup
shells must be Ready/connected before the smoke dispatches. No production change
or deadline relaxation is required for this gate.
