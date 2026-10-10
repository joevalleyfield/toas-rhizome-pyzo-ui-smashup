# Local profile compatibility, 2026-10-10

[Task 039](../../tasks/open/039-local-profile-compatibility.md) accepts the local
fresh/migrated profile slice of Stage 7. The pristine control is the exact local
upstream baseline, not a claim about the latest upstream release. Configuration,
tools directories, command servers, workspaces, recovery and kernel reports use
disposable fixtures. No user profile or existing checkout is used as input.

## Observed repairs

The controls exposed six bounded gaps in the fork:

- A profile without a peer layout was treated as a fresh install, skipping
  its legacy editor list and configured tools. Factory defaults now require an
  empty compatibility file/tool list.
- Legacy import assigned main/history markers to the initiating host even
  when contextual load created a different pane. Markers now address the
  actual editor host.
- Pinned-file confirmation ran after peer application shutdown had committed.
  The explicit committed-close path asserts clean native text and never opens
  another dialog. Ordinary legacy prompts and peer pane/frame pin refusal remain.
- Modern restoration read cursor/selection/scroll but omitted the view's pin.
- The Pin/Unpin menu changed the widget but omitted the bound registry view.
- Peer teardown exported its empty editor set into the legacy compatibility
  list. Peer lists now persist through modern resources; the originating file
  list remains readable in upstream/QtADS mode. Contextual find state still saves.

The task records each state/assertion gate. Before-repair logs retain the
[startup failure](profile-compatibility-2026-10-10/migration-startup-before.log),
[main/close failure](profile-compatibility-2026-10-10/main-and-pinned-close-before.log),
[blocked-close stack](profile-compatibility-2026-10-10/pinned-close-stack.log),
[pin restoration failure](profile-compatibility-2026-10-10/pin-restore-before.log),
and [pin/archive write failure](profile-compatibility-2026-10-10/pin-write-and-archive-before.log).
Early probe API mistakes appear in the first log and are not product failures.

## Accepted checks

- **4 compatibility controls pass**, 33.07 seconds in the persistent fixture
  runtime, and **4 pass**, 33.62 seconds using the final online user command.
  [Matrix log](profile-compatibility-2026-10-10/compatibility-pass.log),
  [user-command log](profile-compatibility-2026-10-10/user-command-pass.log).
- Three positive matrix controls exercise **19 startup processes**: fresh
  upstream, legacy QtADS and peer; actual same-PID exec Restart; subsequent
  launch; upstream/QtADS migration into peer including actual Restart; original
  mode fallback; and peer reopening after fallback. Every process waits for a
  real Ready kernel and executes file text through the production shell API.
- Assertions cover two named sources including UTF-8 BOM/CRLF, main designation,
  pinned view, cursor positions, two live tools, indentation preference and
  unknown nested config. Byte and nanosecond modification-time comparisons
  show no source writes, including parent checks after each process exits.
  Fallback leaves the complete peer persistence tree's
  digest unchanged. Both migrations retain their original config archive.
- A twentieth, negative process injects a Qt callback assertion: exit 1,
  failure marker, no successful Quit marker. Internal/external deadlines and
  cleanup target only the owned process group. Host assertions distinguish
  vanilla QMainWindow, legacy QMainWindow/QtADS, and peer QtADS without QMainWindow;
  source-path assertions verify the selected checkout.
- **701 coordinated tests and 351 subtests pass**, 27 intentional skips,
  two existing high-DPI deprecation warnings, 6.89 seconds.
  [Unit log](profile-compatibility-2026-10-10/units-pass.log).
- **All 22 existing live controls pass**, 106.44 seconds: editors, kernels,
  tools, Selection/Run/debug/postmortem, movement/lifecycle, recovery, retained
  restore, ingress, scale, multi-workspace restart, zero-frame and shutdown.
  [Live log](profile-compatibility-2026-10-10/live-pass.log).
- Seven changed Python files compile under Python 3.12. New-source scoped Ruff
  and root/nested whitespace checks pass.
  [Source checks](profile-compatibility-2026-10-10/source-checks.log).
  The reviewed context inventory is
  **723 references** (six added import/identity bridges), with existing ownership
  classifications retained and a new PROFILE effects proof. The state/config
  census remains 70 rows; no new setting or persistence schema is introduced.

An initial coordinated run failed the intentionally stale inventory review;
the refreshed Python 3.12 review passes. A subsequent run crashed during
collection because the new test imported QKeySequence constants before creating
a QApplication. The test now imports after application initialization; the
complete suite passes. Both failed logs are retained for provenance, not acceptance.

## Revisions and limits

- Coordinating baseline: `609fbfad29f2d34d4575c364b18672cf938f5253`.
- Coordinating implementation: `93be43e502dddedcc6ba2fc448737bbfa3d431c9`.
- Accepted Pyzo: `c956237aa6cf53a0cea21b286d8ee6518d814d8c`, parent
  `99f585fe33cb806378269809fcc27a9add93cc93`.
- Pristine upstream: `26c2c32778dddf8fca3c1a44112941b22f075264` (Pyzo 4.21.0),
  exported read-only with git archive because jj has no archive command.
- Binding base: `764eb4a487abccb162dcbee1a8f0383916561e0e`; pre-existing dirty
  snapshot `b8d9c0a784db678227833ef8e545765a974ad4cb` remains unchanged.
- Embedded native QtADS HEAD `244157db5bdffdf9d250e58a6edf8ee6acfd3a61`, with
  no tree diff from the earlier recorded `243aa54b4f131212ce02ce78b347a13cb3713736`;
  reference checkout `59d4730119466e02195f1a221a54386a9410b16f`. Neither was edited.
- Python 3.12.13, PySide6/Qt 6.11.1, IPython 9.17.1, macOS 27.0.1 arm64.
  Wheel SHA256 `2243093d5518a0c8c13fbcc574f734690c631f508f1755de30f8d0288d28db20`.
  [Runtime record](profile-compatibility-2026-10-10/runtime.json).

The completion/checklist commit follows the recorded implementation commits.
Nothing was pushed.
The bindings and user settings were not changed.

This accepts representative local profiles and the existing integrated replay,
not every possible historical profile or third-party extension. Legacy window
geometry cannot become an identical peer layout; peer default placement is the
accepted migration fallback. Named-view translation and arbitrary extension
compatibility do not enter this slice. Native Windows/Linux validation and the
remaining complete Stage 7 requirement/platform matrix are still open. Physical
macOS coverage limits recorded in task 037 remain explicit.

## Replay steps

1. From the repository root, run the online command below. It needs the recorded
   baseline object and existing local wheel; no cache-warming ceremony or app
   launch is needed. The fixture profiles are temporary and kernels are real.
2. Expect `Ran 4 tests` and `OK`, including an intentional callback-failure
   process that the harness verifies exits 1.
3. Review this evidence and task 039 for the exact accepted slice and platform
   gates. `--offline` is optional only after dependencies are available.

```sh
RUN_LOCAL_COMPATIBILITY_ACCEPTANCE=1 \
  ./.codex-local/bin/uvt run --python 3.12 \
  --with PySide6==6.11.1 --with ipython==9.17.1 \
  --with ./deps/pyside6-qtads/dist/pyside6_qtads-5.0.0.1.dev10-cp310-abi3-macosx_26_0_arm64.whl \
  python -m unittest spikes.peer_frames.test_local_profile_compatibility -v
```
