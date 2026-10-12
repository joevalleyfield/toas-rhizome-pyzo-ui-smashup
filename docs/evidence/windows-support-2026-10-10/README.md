# Native Windows replay, 2026-10-10

Windows 11 x64 build 26200; Python 3.12.13; Qt/PySide6 6.11.1;
IPython 9.17.1; VS 2022 17.14.41 / MSVC 19.44.35229.

Native setup/build/import passed. Unit replay: 699 passed, 13 failed (WinError
1314 symlink privilege), 27 skipped. Live replay: 16 passed, 10 failed.
The final complete reports supersede earlier isolated passes for acceptance.

Visible fixture reached windows-platform readiness with two workspaces and two
ready shells. Physical checklist remains open. Developer Mode is unchanged.

See [the worklog](../../../tasks/open/041-windows-support-replay.md) for fixes,
source pins, dependency patch reproduction and remaining acceptance work.
Raw outputs intentionally retain exceptions and failures.

## Optional symlink policy follow-up

User decision: symlinks requiring extra Windows privileges are outside required
platform support. Updated unit replay: 699 passed, 40 skipped. Historical unit
failures above predate this policy; units-optional-symlinks.xml is current.
Live ingress skips only the alias check, then still fails on a removed-workspace
runtime lookup. This preserves the ordinary ingress acceptance failure.
