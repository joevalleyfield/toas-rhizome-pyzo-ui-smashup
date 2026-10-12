# Windows restart handoff

Windows 11 x64, prepared Python 3.12.13 / PySide6 6.11.1 runtime.

- restart-focused.log/xml: peer and legacy restart and migration, failure controls,
  argument/launch regressions; 7 passed, 1 unchanged upstream restart failure.
- vanilla-migration.log/xml: pristine save/quit, reopen, migration, fallback;
  1 passed, 24.09s.
- units.xml: full final units; 714 passed, 42 skipped, 38.75s.
- full-replay.log/live.xml: final full replay (added after completion).

The pristine baseline is exported read-only from commit
26c2c32778dddf8fca3c1a44112941b22f075264. Its native Windows os.execv restart
failure remains an explicit failing assertion. Fork restarts must prove actual
successor state, kernel execution and quit; clean parent exit alone is insufficient.

Final coordinated replay: 714 unit passes, 42 skips, two warnings (38.75s);
26 live passes and one unchanged upstream native restart failure (398.84s).
Eight-workspace restore passed in 53.860s under the unchanged 60s deadline.
The overall bootstrap command remains nonzero because the upstream control fails.
All patched-application live controls pass. Physical desktop/PDF acceptance and
fork patch integration into accepted source pins remain outstanding.
