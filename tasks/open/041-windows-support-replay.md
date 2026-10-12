# Native Windows support replay

## Status

In progress, 2026-10-11. Continue the public bootstrap handoff on a native
Windows x64 desktop and repair reproduced platform gaps. Stage 7 and physical
interaction acceptance remain open until their checks pass.

The dependency fixes are now integrated in published commit
`93d3f97f66d00cd4964a14a44c588cc3be403935` and pinned by the coordinator.
[Pyzo draft PR #1](https://github.com/joevalleyfield/pyzo/pull/1) targets the
previously pinned peer-frames branch. Earlier manual-patch instructions below
describe the pre-integration state; fresh setup needs no patch application.

## Reproduced gap and change

Both `RecoveryStore` and `WorkspacePersistenceStore` attempted POSIX directory
`os.open` / `os.fsync` barriers on Windows. This reproduced the hosted migration
failure and also blocked ordinary recovery commits. A shared platform helper
keeps POSIX directory barriers and omits the unavailable CRT directory operation
on Windows. Record/manifest file flushes and atomic publication remain mandatory;
flush failures still preserve the previous generation and propagate as store
errors. Windows directory-entry power-loss durability is not established; see
the [platform guide](../../docs/platform-bootstrap.md#windows-persistence-guarantees).

The context audit also used locale decoding and native path strings/order.
Windows therefore reported reviewed sources as changed. Use Python source
encoding detection and portable relative paths/order; the original inventory
now matches all 723 reviewed references without regenerating its acceptance.

Two upstream IPython Run tests expected mixed-case directory strings although
production intentionally uses `os.path.normcase`. Their expectation now uses
the existing platform policy. The local dependency test edit is preserved in
[a root-owned patch](../../docs/patches/windows-pyzo-support.patch),
because `deps` is ignored by the coordinating repository. Production fork pins
are unchanged. To reproduce: run setup on clean sources, then apply the patch
from `deps/pyzo` with `git apply --ignore-whitespace ../../docs/patches/windows-pyzo-support.patch`.
Setup deliberately refuses that modified dependency until the patch is reverted
or integrated into a new accepted fork revision.

## Local replay

- Fresh clone at `C:\Users\tim\Work\toas-rhizome-pyzo-ui-smashup`.
- Windows `py` launcher absent; an existing uv-managed Python 3.12 invokes the
  bootstrap. Prepared runtime is pinned Python 3.12.13.
- VS 2019 was installed initially; user authorized installing VS 2022 C++ Build
  Tools. Installed VS 2022 17.14.41, MSVC 19.44.35229 and Windows SDK 10.0.26100.
- All three pinned source clones obtained online; Qt 6.11.1 MSVC2022 SDK
  downloaded locally.
- Sandbox-created temporary clone directories needed inherited ACLs restored
  and repository-root/Git-directory ownership assigned to the desktop user
  before the unsandboxed native build could reuse them. No global Git trust
  exception was added.
- Invoke `setup` with the host Python, not `.platform/environment`'s Python;
  Windows locks that executable while uv tries to recreate the environment.
- Focused tests in the prepared runtime: **44 passed** in 17.66 seconds.
  Report: `.platform/reports/windows-persistence.xml`. Includes recovery,
  workspace persistence, legacy selection, platform barrier/error handling,
  checkout safety and native Windows Job Object/exec successor cleanup.
- Audit/Run regression replay: **27 passed** in 7.23 seconds.
- Native setup/build/import passed. Wheel:
  `pyside6_qtads-5.0.0.1.dev10-cp310-abi3-win_amd64.whl`; SHA256
  `d105aceaf51b9b4376db57dfe645eff019a250d4393820b851f6b2d493978bce`.
- The desktop account lacks symbolic-link creation privilege (WinError 1314).
  User explicitly chose to leave Developer Mode unchanged and record the
  prerequisite initially. The later user decision makes this affordance optional;
  the initial failures are retained as historical evidence.
- Initial final application unit replay: **699 passed, 13 failed, 27 skipped** in 38.30
  seconds. All 13 failures are real symlink creation controls blocked by WinError
  1314. Audit, persistence and Run controls pass. Opt-in live controls and the
  unused stock-QtADS capability are the recorded unit-phase skips. Logs:
  `.platform/units-windows-final.log`, `.platform/reports/units.xml`.
- Live-kernel controls run separately with the bootstrap's same environment,
  suites and deadlines because the known unit prerequisite failures prevent
  the ordinary bootstrap command reaching its live phase.
- Visible launch reached `PHYSICAL DESKTOP SESSION READY windows`. Snapshot
  reports Physical A and Physical B, each with a ready Python 3.12 shell.
  Fixture: `.platform/desktop-windows`; supervisor remains running for UI use.
- Final full live replay: **16 passed, 10 failed** in 259.73 seconds.
  Unlike isolated controls, full close/debugger replay still encounters callbacks
  resolving removed workspace runtimes. Selection execution reports invocation
  ownership failure. Scale detects deleted-action callbacks even at one workspace.
  These failures remain acceptance blockers; focused passes do not supersede them.
  Evidence: [retained logs and JUnit reports](../../docs/evidence/windows-support-2026-10-10/).
  This replay predates the optional-symlink policy below.

Physical docking/focus/ingress/scaling and UI quit/restart require the desktop
checklist. A passing offscreen test does not close those obligations.

## Additional Windows gaps repaired

Windows venv launchers can have a different PID from their interpreter. Close
and debugger controls now resolve kernel PIDs against the owned process tree.
Forced-crash controls use Windows TerminateProcess on themselves to avoid CRT
DLL teardown access violations; normal application restart remains separately
measured. Scale RSS uses pinned psutil rather than the Unix `ps` command.

A backend-local chrome refresh retired actions belonging to other loaded
workspaces. Pyzo now reconciles menus/status against frames from every loaded
workspace. The dependency patch includes this production fix and a regression
control, as well as the two Run expectation corrections. Selection assignment
invokes the menu belonging to its actual frame. Its live control passes.
The context review's 230 changed line positions track the production edit;
all 723 semantic reference identities and review classifications are preserved.

Focused live recovery/close/debugger regression: 4 passed in 38.89 seconds.
Frame census and live selection regression: 2 passed; application smoke still
failed. Neither deadlines nor failure assertions were relaxed.

## Remaining acceptance work

- Symlink creation privilege is optional and is not a Windows acceptance gate.
  Developer Mode remains unchanged.
- Menu/action retirement, close/debugger callbacks and selection invocation
  ownership now pass. Diagnose the remaining application-smoke wait-run deadline.
- Scale seed/restore now passes at 1, 4 and 8 workspaces. Diagnose the remaining
  automatic tool contextual-state phase before tool-state acceptance.
- Repair Windows restart lifecycle: successor state/kernel/quit verification
  can complete while the parent CRT exec path exits with an access violation.
  Peer, legacy and pristine upstream profile controls remain separate evidence.
- Complete the physical desktop checklist, including docking, focus, file
  ingress, scaling and quit/restart. Visible readiness alone is not acceptance.
- Integrate the dependency patch into the fork and update the accepted source
  pin before claiming a clean-clone bootstrap includes these fixes.

## Optional symlink policy (user decision)

The user explicitly excluded affordances requiring unusual Windows permissions
from required platform support. Symlink unit controls now skip only actual
Windows WinError 1314. If creation succeeds they run normally; other errors fail.
The live ingress probe skips only alias reopening, retaining ordinary ingress,
close reentrancy and empty-workspace checks.

Replayed unit suite: **699 passed, 40 skipped**, 2 warnings, 40.00 seconds.
The 13 additional skips are symlink controls. A separate capability regression
suite verifies narrow error handling. No privileges or system settings changed.

Live ingress replay passes the symlink point with an explicit optional skip,
then fails on callbacks/lookup for a removed workspace runtime. This remains
an ordinary Windows acceptance defect, not a symlink prerequisite.
The dependency patch now also includes the two optional-symlink test changes.

## Frame menu width (2026-10-11)

User observed two menus followed by overflow despite a wide frame. The overlay
QMenuBar was parented outside the QtADS layout but never assigned frame-width
geometry. It now tracks show/resize events and reserves its height using the
original frame margins. Shared native menus are unchanged. Menu/status controls:
19 passed, including a real-frame regression that fits all titles across three
widths. Existing application processes require relaunch to load the change.

## Menu/workspace retirement (2026-10-11)

Menus held subscriptions to application keymap and workspace editor/shell/tool
signals beyond their frame lifetime. ShellCommandProjector also evaluated a
menu's shell provider before detecting a deleted QAction, which could resolve a
runtime after it had been removed from the catalog.

Menu.dispose now explicitly disconnects external subscriptions and unregisters
its shell projections. Frame projection removal disposes all native menus;
workspace context retirement removes per-frame menus before retiring the owner.
The shared native application menu is retained. Shell refresh validates the
action before invoking its provider. Unexpected live-provider errors still fail.

Focused live close, debugger and ordinary ingress replay: **3 passed**, 33.20s.
Menu retirement regression + shell/menu projection controls: **16 passed**.
Full bootstrap unit phase: **705 passed, 41 skipped**, 2 warnings, 37.83s.
Initial full live phase: **19 passed, 7 failed**, 229.75s.
Final replay after the additional native ownership repair is recorded below.

The 723 context-reference identities and their classifications remain intact.
Reviewed scope hashes changed for buildMenus, FileMenu.build and context retire
because cleanup was added; owner-routing semantics remain the existing ones.
Lifecycle regression tests were added to the relevant acceptance proof lists.
The root dependency patch was rebuilt and reproduced all nine edited/new files
from pinned source snapshots.

### Native action lifetime follow-up

The first cleanup fixed close/debugger/ingress but scale still found invalid
Reload action wrappers in a live File menu. Menu actions now use explicit
QAction construction with their menu as parent rather than Qt's convenience
addAction overload. Scale seed/restore now passes at 1, 4 and 8 workspaces:
**1 acceptance test passed**, 117.17s; eight-workspace restore took 53.484s
within the unchanged 60s deadline. Raw output retains Windows COM/PDF diagnostic
stacks; physical PDF acceptance is not established by this run.

Native frame DeferredDelete/Destroy events retire menus before child actions.
Native Menu destruction also disconnects connection handles, which are safe
when Python Qt wrappers are already invalid. Guarded delivery rejects queued
callbacks after retirement. Four menu lifecycle regressions cover explicit,
native and queued retirement and dead-action provider rejection. A real frame
regression checks retirement occurs before child action destruction.

Final full unit suite: **708 passed, 41 skipped**, 2 warnings, 38.51s.
The execution probe now uses the invoking B frame's menu on per-frame platforms;
shared native menus still resolve B through foreground invocation. Ownership,
nested-dialog and real-kernel assertions are preserved. Final full live replay:
**21 passed, 5 failed**, 330.00s. Close, debugger, ingress, selection and scale
pass in the complete replay, not just isolated controls. Remaining failures:
application smoke wait-run, automatic tool-state phase, and peer/legacy/pristine
restart parent exit status. No test assertions or deadlines were relaxed.
Retained evidence: docs/evidence/windows-menu-lifecycle-2026-10-11.


## Application smoke and Windows debugger paths (2026-10-11)

The smoke closed its selected second shell and implicitly expected the older
shell to become the execution target. Production deliberately refuses that
fallback. The smoke now explicitly selects the remaining shell pane and checks
that each Run request returns provenance rather than waiting for a refused run.

A real Windows defect was exposed next: debugger filenames are normalized by the
kernel, but the captured source map used their original spelling. Line markers
and captured-source navigation now match using platform normcase while retaining
document identity and owner checks. Canonical registry lookup also respects
platform casing. The regression simulates Windows spelling and proves that both
same-owner views update while the other workspace remains untouched.

The peer smoke polls at 100ms instead of 500ms within the unchanged ten-second
budget. It waits for asynchronous marker projection and the traceback source
receipt before post-mortem re-entry. Its exact line/frame assertions remain.
After verifying two-kernel affinity and working-directory preservation, the
kernel leaves the temporary directory before termination so Windows cleanup can
remove it without racing asynchronous process exit.

Full units: **709 passed, 41 skipped**, two warnings, 38.90s. Peer + legacy smoke
and intentional timeout/exception controls: **2 passed**, 43.85s. The final
focused debugger/live replay is recorded in the evidence directory below.
All 723 audit reference identities/classifications remain intact; only reviewed
smoke/startup scope hashes and following line positions changed. The dependency
patch reproduces all eleven edited/new files from the pinned source snapshot.
Remaining previously failing controls: automatic workspace tools and the three
restart parent statuses. A full live replay has not been repeated for this step.
Evidence: docs/evidence/windows-application-smoke-2026-10-11.

Final focused replay: **18 passed, 1 optional symlink skip**, 62.86s.
Includes debugger unit regression, complete owner audit, peer/legacy smoke,
intentional failure controls, live workspace debugging and fresh-process overlay
restore. Root and dependency diff checks are clean.


## Automatic contextual checkpoints and tools restore (2026-10-11)

The automatic tools phase exposed a product defect: the retention coordinator's
capture contained only document resources. Once those resources were durable,
preference/history/tool-state changes compared equal and were silently skipped,
even though live zoom/status projection had correctly updated both owners.

Checkpoint generations now capture documents and each loaded workspace's
contextual snapshot together. The writer publishes those captured profiles,
so changes after capture cannot alter the queued generation. Normal explicit
save/close paths continue to capture current profiles. The regression proves
context-only saves for two owners with unchanged document text, immutable
capture across subsequent mutations, and suppression of redundant saves.

Automatic publication completes in **1.078s**, within the original four-second
assertion. All ten independent built-in tools, held stale replies, Cancel and
publication-failure preservation, A teardown/resume and surviving B kernel
checks pass. A fresh process restores both owners' requested configuration,
histories, tool states, shell profiles, project settings and affiliation.
The project fixture now seeds platform-normalized paths, matching the file
browser's established configuration format; restore equality remains exact.

Focused retention regression/scheduling + tools replay: **11 passed**, 31.84s.
Full units: **710 passed, 41 skipped**, two warnings, 39.16s.
Broader real-process retention acceptance: **9 passed**, 67.19s, including forced
crash recovery, failed publication, sustained checkpoint and restart restore.
The context audit now has **724 references**: one capture access moved out of
startup and two explicit capture-service accesses were added with CONTEXT proof.
Other classifications are preserved. The dependency patch reproduces all twelve
edited/new files from the pinned source snapshot. Diff checks are clean.

Evidence: docs/evidence/windows-workspace-tools-2026-10-11.
Remaining from the prior full live replay: peer, legacy and pristine restart
parent status failures. No full live-suite rerun was performed for this step.


## Windows restart handoff (2026-10-11)

Windows os.execv launched a valid successor, but its CRT teardown crashed the
old live Qt process and reported an error parent status. Patched peer and legacy
restart now launch the successor with an argument list, retain the original
standard streams, and request normal Qt event-loop exit. CREATE_NO_WINDOW avoids
a new console window. POSIX retains exec replacement. Cancel and save barriers
remain before process launch; launch failure propagates instead of reporting a
clean exit. No forced process termination is used for application restart.

Unit regressions cover ordinary/frozen arguments with spaces, embedded quotes
and an empty argument; launch-before-exit ordering and original stream handoff;
launch failure; and the POSIX exec path. The live compatibility probe explicitly
checks a new Windows PID plus the retained restart token, restored state,
real-kernel execution and successor quit markers. It still checks same-PID exec
on POSIX and rejects missing successor evidence even if the parent exits zero.

Focused compatibility replay with the final handoff: **7 passed, 1 failed**,
48.33s (four unit regressions and four compatibility controls). Peer restart,
legacy restart/migration/fallback and injected callback failure pass. The one
failure is the **unchanged pristine upstream baseline** native Windows restart
at 26c2c32778dddf8fca3c1a44112941b22f075264, still crashing in os.execv.
That assertion is retained as a reported failure, not skipped or marked accepted.

An independent pristine save/quit profile control exercises vanilla reopen,
peer migration/restart/reopen, vanilla fallback and peer reopen using unchanged
upstream sources: **1 passed**, 24.09s. It keeps migration coverage complete when
the separate upstream native restart control fails. Source bytes/mtime and
workspace persistence digest checks are preserved.

Final full unit phase: **714 passed, 42 skipped**, two warnings, 38.75s.
All 724 ownership audit identities/hashes/classifications are unchanged (only
line positions updated). The dependency patch reproduces all thirteen edited/new
files from the pinned snapshot. Final full live replay is recorded below once
complete. Evidence: docs/evidence/windows-restart-2026-10-11.


### Final coordinated replay

Full live phase: **26 passed, 1 failed**, 398.84s. The only failure is
`test_vanilla_profile_migration_and_fallback` at unchanged upstream native restart;
the separate vanilla save/quit migration/fallback control passes. All patched
application controls pass together, including peer/legacy restart, tools restore,
selection, close, debugger, ingress, recovery and 1/4/8-workspace scale.
Eight-workspace restore: **53.860s**, under the unchanged 60s deadline.
The overall bootstrap test command still returns nonzero for the upstream control.
Raw PDF/COM diagnostics remain retained; physical PDF acceptance is not implied.
Root/dependency diff checks are clean. No source pins, commits or PRs changed.

Next work: integrate the dependency patch into the fork and update accepted pins;
complete native desktop interactions, especially restart with retained text,
keyboard/menu/DPI behavior, OS file delivery and PDF export. The upstream native
restart control remains a separately visible dependency/runtime compatibility gap.


## Integrated native desktop replay (2026-10-11)

The Windows dependency repairs are published on codex/windows-support and pinned
by platform-sources.json. Draft Pyzo PR #1 targets codex/peer-frames. Setup rebuilt
the pinned QtAds wheel successfully. A separate clean clone fetched the source
revision; final source-pin verification and coordinated results follow below.
The retained dependency patch is historical, against c956237, not an extra setup step.

Native Windows discovery found floating frames owned by the hidden manager were
missing normal taskbar/window behavior. Real Windows QPA frames now have independent
native ownership, copied manager styling and minimize controls, retaining their
QtAds manager and retirement lifetime. Each loaded runtime subscribes once to
settled chrome and user focus. Secondary shell frames now have complete menus.
Refresh after final application exit no longer resolves a retired workspace.

Native input verified independent frames, maximize/resize/minimize/restore,
full menus, shared editor typing/undo/redo, shell creation and actual kernel
execution, canceled restart and a successful new-PID restart retaining dirty text,
native Open, local New/Run, PDF export content and normal persisted Quit. The native
receipt documents intermediate failures and nonfatal PDF COM diagnostics.
Mixed-DPI/multiple monitors, OS file associations/Explorer drop, tab positions and
cross-frame pane dragging remain physically unverified. Stage 7 remains open.
Evidence: docs/evidence/windows-native-desktop-2026-10-11.

Adding secondary-runtime subscriptions exposed excessive projection work.
Render-generated focus now returns before projecting metadata; real accepted focus
still selects its owner. A measured eight-workspace profile found 276,039 shell
command enabled checks: every new action refreshed all older actions. Registration
now initializes only the new action, while actual state changes still refresh the
full live census. Focus/menu lifecycle regressions: 8 passed. Restored eight-workspace
fixture passes unchanged 60-second acceptance in 42.875s. This is a focused result,
not yet a full integrated-suite result. The profile diagnostic itself is not an
acceptance run (its unavailable-record assertion failed because seed Quit omitted
that loaded record; the acceptance fixture was repaired as the original test does).

The integrated pre-performance replay had 717 units pass, 42 skip and 23 live pass,
4 fail (Run variants, peer smoke, scale, pristine upstream restart). Focus gating
restored Run variants, but smoke/scale still failed; linear action registration
restored scale. A test-only attempt to overlap the second kernel interfered with
single-kernel/post-mortem smoke semantics and was reverted. Deadlines and assertions
were not relaxed. Final full replay is in progress.


### Published integrated replay

Final pin: `93d3f97f66d00cd4964a14a44c588cc3be403935`. Strict bootstrap checkout accepts the clean remote
verification clone at that pin; the historical patch reproduces all thirteen files.
Coordinated unit phase: **719 passed, 42 skipped, 2 warnings**, 53.48s.
Coordinated live phase: **25 passed, 2 failed**, 412.02s. All ordinary patched
application controls pass, including peer/legacy smoke and eight-workspace restore
in **22.328s** under the unchanged 60-second deadline. Failures are the unchanged
pristine native Windows restart and an injected-failure smoke startup timeout;
the latter stopped before the injected callback was reached. Bootstrap remains
nonzero. No acceptance assertion/deadline was relaxed. Evidence:
docs/evidence/windows-integrated-2026-10-11. The isolated failure-control replay
result follows when complete. Draft coordinating PR:
https://github.com/joevalleyfield/toas-rhizome-pyzo-ui-smashup/pull/1.

Isolated injected-failure replay: **1 passed**, 19.41s; timeout and exception
injections both reject the run with nonzero status. No source change between the
coordinated failure and focused pass. The coordinated startup stall is therefore
recorded as intermittent, not suppressed. Both review PRs remain draft; Stage 7
and native hardware/OS delivery checks remain open. Source diffs pass whitespace
checks; raw evidence retains original whitespace.


## Added physical monitor (2026-10-12)

Equal-scale dual-monitor checks now pass: A on the primary display, B manually
moved to the portrait LS27A70 at negative desktop coordinates; native maximize/
restore, eight menus and File popup, minimize/restore, B shared edit and A undo
propagating across displays, and clean Quit (supervisor exit zero). Both displays
report 200% scaling, so mixed-DPI transitions remain unverified. The helper could
not demonstrate border resize; that subcontrol remains open rather than accepted.
Observer-only fields now retain screen/DPI and frame monitor assignment. Syntax
and whitespace checks pass. No production repair or full-suite rerun was needed.
Evidence: docs/evidence/windows-monitors-2026-10-12.

2026-10-12 follow-on physical replay: real primary 200%/portrait 150% exposed
system-awareness startup calls and a restored-frame coordinate gap. Repairs
retain Qt per-monitor awareness and recover unreachable saved title bars. Actual
DPR 2.0/1.5, shared dirty edit retention, native System/Size resize (853 to 419),
four tab positions, native tab reorder, pane float/redock, user physical monitor
disconnect with restore on remaining display, and user Explorer drop into A are
recorded under docs/evidence/stage7-physical-2026-10-12. Resource snapshots verify
document identity/text retention and receiving-owner-only Explorer delivery.
Monitor reconnect remains pending; OS association launch of this checkout was
not configured. User directs retaining portrait 150% and new display arrangement.

Reconnect completed, 2026-10-12: observer confirms primary DPR 2.0 and portrait
DPR 1.5. B returns to LS27A70 at reachable geometry [4430,-1279,417,661]; both
owners retain the identical shared dirty document and view identities, and no
observer errors appear. Native B File menu opens and all eight menus remain
available. Clean native Quit confirms termination of the test-owned shell;
about-to-quit reports no errors and launch supervisor exits zero. Fixture is now
closed. User's 150% portrait / 200% primary configuration remains in place.
This completes the requested mixed-DPI/reconnect/resize/Explorer/pane/tab physical
checks; resize was verified through native System/Size, not the unsuccessful
border-drag attempt. OS file-association launch was not configured or claimed.
