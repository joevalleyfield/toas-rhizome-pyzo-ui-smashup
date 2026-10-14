# macOS callback lifetime repair, 2026-10-12

As Engineer, implemented the two repairs after the user explicitly confirmed
proceeding following [task 044's state/assertion gate](../macos-callback-retirement-2026-10-12/README.md).

## Change and identities

Pyzo revision `6d6b8b6c789f12b33f8afb4276f99e25fbd8bd79` contains the repairs
and 51 new regression cases. [Dependency draft PR #3](https://github.com/joevalleyfield/pyzo/pull/3)
targets `codex/peer-frames`. [Integration draft PR #3](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/pull/3)
pins that exact revision. Neither PR is merged in this repair pass.

- Checkpoint timer: stop before exit negotiation; resume only if it was active
  and exit returns to idle. The callback rejects work throughout exit and
  rechecks flags/owner membership after each snapshot and preference callback.
  A queued callback cannot reach disposed owners just because timer stop cannot
  revoke its delivery. Canceled exits retain normal future checkpointing.
- Broker observer: clear current broker identity and unbind before committed
  shell cleanup. Queued old events fail the identity check; callbacks after
  native Qt deletion return before touching cursors/widgets. Current live
  disconnects retain error text/read-only behavior and unrelated failures remain
  visible. Reconnect identity handling is preserved.

The required context-consumer review is updated at integration revision
`822139b046de0be2b54be01323fe4477aa0b2b62`. All 724 semantic references retain
their classifications/proof associations. Four fingerprints change: checkpoint,
two committed-close references, and the enclosing shell module's fingerprint.
Reviewed proof entries now include the new lifetime tests. Line locations are
regenerated against the exact new source; the audit assertions are unchanged.

## Verification cycles

1. [Checkpoint before](checkpoint-before.log): 27 fail, 14 pass against original
   source. Initial repair passes 41 new tests plus 18 existing policy controls.
   Returning to the C7 state analysis identified the multi-owner ordering case:
   A's snapshot can begin shutdown before B's snapshot is attempted. The added
   case [fails before the per-owner recheck](multi-owner-before.log) and all
   [60 checkpoint/policy controls pass afterward](checkpoint-final.log).
2. [Shell before](shell-before.log): seven failures/seven passes. Real Qt native
   deletion, real queued Yoton events and terminate/flush/context-close failures
   expose the old observer lifetime. [Final focused controls](focused-after.log):
   79 pass, including checkpoint, shell, menu and application lifecycle cases.

The diagnostic native widget is a minimal QPlainTextEdit carrying the actual
PythonShell methods, rather than a kernel-starting PythonShell constructor.
Live integration controls supply the full shell/kernel coverage. The existing
identity-control fixture now uses a real QObject so native validity is testable.

## Actual hosted experiment

[Run 38321395657](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38321395657),
job `115050064395`, tests integration revision
`79bc5933d381fd7d060ab7784a671a314f724845` and repaired Pyzo `6d6b8b6c`.
Build and experiment both succeed. [Raw hosted artifacts](hosted/identity.json)
retain every result.

The runner again reports VirtualMac2,1, three virtual M1 CPUs and 7 GiB memory.
Initial load averages are 20.217/17.578/8.048; available memory is 3,778,691,072
bytes. Python is 3.12.13, macOS 15.7.9 arm64. This establishes testing under
reported VM constraints; it does not establish hardware as the original cause.

| Hosted control | Result | Elapsed |
| --- | --- | --- |
| Unchanged close/debugger round 1 | Both pass | 15.7313s |
| Unchanged close/debugger round 2 | Both pass | 17.9486s |
| Unchanged close/debugger round 3 | Both pass | 16.1006s |
| Observed close, original 35s deadline | Pass, no diagnostic exceptions | 5.4049s |
| Observed debugger, original 35s deadline | Pass, no diagnostic exceptions | 7.9748s |

All five log files contain none of the forbidden diagnostic markers. XML
independently verifies six original test passes. All 28 observed queries have
success status 4; maximum observed wait is 0.148929s. Timing differences from
the preceding run are observations, not an established performance effect.

## Full local and hosted acceptance

Local replay uses fresh exact dependency checkouts and the existing working
cached Python/Qt runtime, reused without package mutation. It runs the original
bootstrap-only and fail-fast commands. Six bootstrap tests pass/one Windows
control skips. The first full run correctly fails the exact-source consumer
audit; after review reconciliation, 782 units pass/30 skip/two warnings.
All 27 live controls pass in 156.16s, including close/debugger and all profile compatibility/reopen controls. XML independently verifies these totals.

The strict local experiment passes its unchanged close/debugger pair and both
observed probes. [Local evidence](local/local-repair-experiment.log) retains the
8.8945s pair, 2.9069s observed close and 5.0828s observed debugger results.

The initial hosted platform run at `79bc5933` encountered the same inventory
gate and was superseded by the audited revision. Full canonical hosted
acceptance is dispatched at `822139b0` as
[run 38321657867](https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/actions/runs/38321657867).
Its macOS job `115051151543` succeeds: six bootstrap passes/one skip, 782 units/30 skips/two warnings and all 27 live controls in 270.14s. Fresh native build, exact manifest pin and XML totals are independently verified in hosted-acceptance/. Windows passes seven bootstrap controls and 784 units/28 skips, then fails peer smoke after eleven live passes at wait-affinity-seed. The overall workflow remains failed because Windows and Linux remain unresolved. Linux builds and passes 782 units, then fails the unchanged Run variants control after nine live passes. The failed Run Cell boundary is line 195: `assert value(sa, "'never_run' in globals()") is False`. The returned value is not logged, so execution failure versus query timeout is unresolved. It is retained as adjacent evidence in hosted-linux-job.log; no Linux repair is made.

## Limits and adjacent observations

Original acceptance controls, deadlines and primary platform workflow are
unchanged. No Windows-specific fix, merge, virtual-hardware emulation, CPU
stress or visible desktop acceptance is performed. The historic PID wait was
not reproduced or repaired; successful samples do not prove that it cannot
recur. Task 041/Stage 7 remain open. The generated local runtime's unexplained
hidden Qt plugin flags remain separate; this repair pass uses the cached
working runtime locally and a fresh canonical build on GitHub.
