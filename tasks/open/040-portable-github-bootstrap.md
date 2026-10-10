# Portable GitHub source handoff and platform bootstrap

## Status

CLAIMED by Codex, 2026-10-10. User explicitly requested a script that clones
the repositories and authorized publishing this work to GitHub.

## Scope

Publish the coordinating repository and accepted Pyzo, binding and native QtADS
revisions to the user's GitHub account. Add a pinned clone/build/test/visible
fixture entry point for Windows, Linux/WSL and macOS, with no Mac-local paths,
wrapper or cache requirement. Preserve pre-existing binding packaging changes.
Add Windows/Linux CI using the same entry point. Native desktop acceptance stays
open until observed on those desktops.

Allowed writes: bootstrap scripts/manifest/docs/workflow, owned subprocess
support, harness launcher and restart assertions, physical fixture platform
selection, this task and completion evidence/checklist. No production behavior
change is planned. Publishing exact reviewed sources is authorized.

## Pre-edit state/assertion coverage

The user's current implementation request and standing carte-blanche authorize
the bounded harness portability changes below.

| State | Handling / executable assertion | Before |
| --- | --- | --- |
| New dependency checkout | clone exact reachable revision; `HEAD == manifest commit` | unavailable remote forks |
| Existing exact clean checkout | reuse; `HEAD == commit and status == empty` | Mac-local only |
| Wrong revision, dirty files, foreign remote or interrupted checkout | fail with path; `tree unchanged after rejection` | no handoff policy |
| Runtime absent / prepared / failed build | owned environment, pinned dependencies, platform wheel; import capabilities and versions before marking setup complete | one Mac wheel |
| POSIX probe exit / timeout / assertion / surviving child | session group termination; child cannot survive cleanup | POSIX helper already present |
| Windows probe start / exec successor / timeout / assertion / surviving kernel | stdin gate before assignment to kill-on-close Job Object; no child code before ownership; descendants die at teardown | `os.killpg` unsupported |
| Restart on POSIX / Windows | POSIX keeps PID; both carry a unique restart receipt and verify state/kernel/Quit markers | same-PID-only assertion |
| Existing persistent runtime / legacy local wrapper | use current pinned Python when selected; default online pinned wrapper fallback | forced offline cache |
| Visible desktop / offscreen / missing display | fixture asserts requested actual QPA backend; launch rejects offscreen; desktop checklist records platform | Cocoa-only fixture |

Verification: local bootstrap safety/process controls, current coordinated and
live suites, fresh remote clone/bootstrap/test/visible smoke on this Mac, and
actual hosted Windows/Linux builds/tests. CI is automated platform evidence,
not physical docking/focus/drop acceptance.

The exited-leader negative control exposed a macOS-only state: after the leader
is reaped, signalling an all-zombie group reports EPERM. A disposable diagnostic
proved signalling succeeds before reaping and reports EPERM afterward. Cleanup
now sends both signals before reaping, is idempotent, and accepts macOS EPERM
only if `ps` proves the group has zero live members. Any live member or any
non-macOS permission failure still raises. Assertion: the descendant's delayed
marker never appears, even when its leader has already exited.

First hosted builds exposed Qt package metadata differences: Linux 6.11.1 names
its archive architecture `linux_gcc_64` (installed directory remains `gcc_64`);
Windows uses per-compiler metadata directories absent from aqtinstall 3.3.0's
recipe. Official directory listings and aqt metadata verify both gaps. Pin the
installer's supporting upstream revision and use the listed Linux architecture.
The first coordinated bootstrap run also exposed the omitted bundled yoton
source path; the accepted suite already documents that path. Include it in the
runtime environment rather than changing Pyzo imports. Verify each change with
the real target build and existing full suite.

Second native builds identified two more setup states: Qt's Linux `qtbase`
archive needs its separate `icu` archive (rcc/qmake explicitly fail to load
libicui18n.so.73), and MSVC fails to create its generated mocs object at the
long coordinating checkout path. Install both listed Linux archives and require
ICU when reusing an SDK; build a temporary source copy at a short path on every
platform. Assertions remain successful native compilation/import and clean
pinned checkouts; no production source change is needed for either failure.
