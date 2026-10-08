# External file-open routing acceptance — 2026-10-07

The local external file-open slice of Experiment 014 Stage 7 is **accepted**
through [033](../../tasks/open/033-external-file-open-routing.md). Stage 7's
integrated compatibility, scaling, final census and physical/platform gates
remain open. The September amendment and its deferrals remain normative.

## Exact implementation and runtime

- Root implementation: `be1f8db4bed48b65736492a634542193e2350d18`, parent
  `223da37a708c3a597ab534a0d14ef5b95a04465a`.
- Pyzo implementation: `0e334f57de142cf4deeee4dd43b5b1453b9ad6f4`, parent
  `6544d31cd7d3562856a57c242f7fd9ea254910db`.
- Binding unchanged: `b8d9c0a784db678227833ef8e545765a974ad4cb`; embedded
  QtADS `243aa54b4f131212ce02ce78b347a13cb3713736`.
  Separate QtADS reference: `59d4730119466e02195f1a221a54386a9410b16f`.
  Preexisting binding packaging changes were preserved.
- Python 3.12.13, PySide6/Qt 6.11.1, IPython 9.17.1 and the existing
  `pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl`.
  [Runtime record](workspace-ingress-2026-10-07/runtime.log).

## Accepted boundaries

| Boundary | Machine-checkable proof |
| --- | --- |
| Foreground routing | All six three-owner focus orders × all eight eligibility combinations; repeated focus; workspace, pane and backend activation; retired history pruning; shutdown exclusion; deterministic loaded-order fallback; bootstrap exclusion. |
| Runtime and close eligibility | Missing/disposed/failed/closing/shutdown MRU owners fall back to the preceding eligible owner. A nonempty but wholly ineligible loaded set refuses visibly and creates no workspace. |
| GUI dispatch | Real command parser/server handler queues one GUI entry point from a worker; a foreground change before dispatch selects B. Bare paths, explicit `open`, spaces, CLI args and a native macOS `QFileOpenEvent` enter the same route. Legacy mode resolves its current editor manager at dispatch. |
| Shared and retained authority | Opening A's unsaved file in B creates a B view of the same durable document and text. CLI, symlink and OS reopen preserve the existing local view count. Missing disk source reopens retained text without creating a user file. Project location does not choose an owner. |
| Recovery dialogue | Captured owner/epoch survive focus changes; Cancel, closing, retirement, reload and application exit prevent publication/load. Legacy recovery publishes only to its captured owner. |
| Actual close reentrancy | A genuine Ready B kernel requires close confirmation; the nested callback opens only in A. Cancel preserves B. After cancellation B becomes eligible again. A sole closing owner refuses a new file with no default creation. Successful retirement and final-owner unload do not reuse retired hosts. |
| Empty loaded set | Startup with no loaded owners creates exactly one default; an opaque unavailable workspace record remains byte-for-byte equivalent in the committed state. |
| Quit/Restart phase | Negotiating, cleaning, finished and exit-requested states reject ingress. Actual cancelled Quit returns to idle and accepts the next open. The exit guard remains set after irreversible teardown. |
| Retired file checks | A focus-queued native external-file callback checks live admission before filesystem/widget access and after reload dialogue. Retired views do not reload or read a foreign context; live/legacy checks continue. |

Source/tests: [coordinator](../../spikes/peer_frames/workspace_coordinator.py),
[routing matrix](../../spikes/peer_frames/test_workspace_ingress.py),
[native dispatch assertions](../../deps/pyzo/tests/test_workspace_ingress.py),
[Qt probe](../../spikes/peer_frames/qt_workspace_ingress_probe.py).

## Verification and repairs

**588 tests and 56 subtests pass** in the coordinating/Pyzo suite. The 18 skips
are 17 opt-in live controls and the stock tab-side expectation superseded by
the pinned fork. The existing two high-DPI deprecation warnings remain.
**All 17 live controls pass** in the final full replay, **61.34s**. Full peer
smoke **10.974s** and maintained-fork legacy smoke **7.648s** pass. All ten
touched Python sources compile and pass Ruff F and trailing-whitespace checks.

Native proof exposed duplicate path registration when the ordinary file
constructor tried to create a foreign owner's shared view. Ingress now resolves
the live canonical resource before using the existing retained-view constructor.
It also exposed a queued file check after owner retirement; admission guards
prevent its stale context access. Source review caught recovery publication
reading foreground after a modal chooser, and cancelled Quit retaining its
exit flag; both have explicit state assertions and bounded repairs.

The prior tools harness twice cancelled B's immediate survivor query after
0.2s, while B stayed Ready and returned the unchanged value on a later query.
The proof now holds one Future in a separate event-loop phase with a two-second
auto-cancel, the original shell/value assertions, and unchanged phase/external
deadlines. The final full replay records a **0.111s** successful B response.
Production kernel behavior was not changed.

Logs: [coordinated](workspace-ingress-2026-10-07/coordinated.log),
[final live](workspace-ingress-2026-10-07/live.log),
[peer](workspace-ingress-2026-10-07/peer.log),
[legacy](workspace-ingress-2026-10-07/legacy.log),
[source checks](workspace-ingress-2026-10-07/source-checks.log),
[tools diagnostic](workspace-ingress-2026-10-07/tools-diagnostic.log),
[tools/restore recheck](workspace-ingress-2026-10-07/tools-final.log).
The initial tools failure and isolated failure are retained in
[initial live](workspace-ingress-2026-10-07/live-initial.log) and
[tools recheck](workspace-ingress-2026-10-07/tools-recheck.log).

## Census delta and remaining limits

L29 is now an explicit application ingress service selecting an eligible W
owner on the GUI thread. The command server reads no peer widget at dispatch;
peer file opens use fixed-owner services, while legacy file opens retain their
global compatibility path. `_start.MyApp.event` delegates to the same parser.
Foreground history is process-local; without focus history selection falls
back deterministically to loaded order. This is a local L29 delta, not a rerun
of the full 70-row or direct-global census. Other command-server operations
remain for the final census.

One earlier full replay exited 139 during debugger restore startup. The faulting
native stack begins in `ads::CDockManager::componentsFactory()` and dock-area
construction through the binding's `addDockWidgetToContainer`. The unchanged
isolated debugger replay and final full replay pass with fault diagnostics
enabled. This observation remains a Stage 7 compatibility follow-up; passing
replays do not prove it eliminated. See [failed replay](workspace-ingress-2026-10-07/live-native-crash.log),
[fault summary](workspace-ingress-2026-10-07/native-restore-crash.log), and
[isolated debugger replay](workspace-ingress-2026-10-07/debugger-recheck.log).

The probes use offscreen Qt, test-owned configuration, a non-listening command
server and deadline-owned processes. QFileOpenEvent exercises macOS application
handling; physical OS delivery/window-manager behavior, Windows/Linux,
unmodified upstream vanilla, representative scaling and complete integrated
restart remain unaccepted Stage 7 obligations. File Move/Fork UX, shell
migration, zombies, synchronization and broad TOAS/Rhizome work stay separate.
Nothing was pushed.

## Reproduction

```sh
QT_QPA_PLATFORM=offscreen PYTHONPATH=deps/pyzo/pyzo:deps/pyzo:. \
  ./.codex-local/bin/uvt run --offline --python 3.12 \
  --with pytest --with PySide6 \
  --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl \
  --with ipython python -m pytest spikes/peer_frames deps/pyzo/tests -q -rs

RUN_LOCAL_RETENTION_ACCEPTANCE=1 RUN_LOCAL_EXECUTION_ACCEPTANCE=1 \
  PYTHONFAULTHANDLER=1 PYTHONPATH=. \
  ./.codex-local/bin/uvt run --offline --python 3.12 --with pytest \
  python -m pytest spikes/peer_frames/test_local_retention_acceptance.py \
  spikes/peer_frames/test_local_execution_acceptance.py -q -s
```
