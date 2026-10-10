# Physical macOS launcher dependency bootstrap

## Status

DONE by Codex, 2026-10-10. User reports that the hard-coded `--offline`
inside task 037's launcher fails with their dependency cache. The existing
request to implement this replay covers its bounded bootstrap repair.

## Scope

Make first-run dependency setup work without a pre-populated cache. Preserve
isolated Cocoa bundle/configuration and the pinned accepted QtADS wheel/runtime
packages. Provide explicit offline replay and actionable setup failures. Update
the user instructions; do not expand physical acceptance or change Pyzo.

## State and assertion coverage before editing

| State | Assertion / desired path | Existing coverage / gap |
| --- | --- | --- |
| Online, cold / warm cache, Python installed / download needed | bootstrap succeeds using ordinary uv resolution; pinned modules import after bootstrap exits | gap: unconditional offline refuses cold cache |
| Offline, warm cache | explicit `--offline` prohibits resolution downloads and produces a persistent runtime | old cached run succeeds; archive-layout dependency remains |
| Offline, missing Python / package / incompatible wheel | exit nonzero with an online retry command and original uv diagnostics | existing raw subprocess exception |
| Runtime environment fresh / already built; dependency installation fails partway | check subprocess result, never publish a successful bundle on failure; retry can populate same owned environment | needs checked venv + pip setup |
| Cache path / internal archive layout changes or cache is cleaned after build | runtime site-packages live under fixture directory; actual imports succeed with empty runtime cache | gap: bundle references archive-v0 paths |
| Live previous fixture / missing or multiple local wheels / non-macOS / missing compiler | existing refuse/build guards remain; no user configuration edits | existing guard paths |

Create a fixture-owned venv with uvt, install PySide6 6.11.1, IPython 9.17.1 and
the existing local wheel (copy link mode), then inspect that environment directly.
Default is online; `--offline` is forwarded only on request. A real cold-cache
bootstrap and explicit offline replay will verify imports and bundle compilation;
focused bootstrap checks cover dependency failure and persistent-path contracts.


## Completion evidence

The launcher defaults to online setup and pins PySide6/Qt 6.11.1, IPython 9.17.1
and the existing local QtADS wheel. `--offline` is opt-in; `--cache-dir` allows an
explicit dependency-cache override. uvt creates a fixture-owned Python environment
and copies installed packages into it, so no runtime path references archive-v0.
Dependency/import failures exit before bundle publication with original diagnostics
and, in offline mode, an online retry hint. Existing app/config/UI setup is unchanged.

Real checks (2026-10-10):

- [Cold-cache online build](../../docs/evidence/physical-bootstrap-2026-10-10/cold-online.log):
  a new cache downloaded the pinned packages and the native bundle compiled.
- [Cold-cache offline failure](../../docs/evidence/physical-bootstrap-2026-10-10/cold-offline.log):
  exit 1, explicit retry message and no `launch.json` success marker.
- [Offline replay with a second empty cache](../../docs/evidence/physical-bootstrap-2026-10-10/offline-replay.log):
  existing fixture packages satisfied setup without downloads; bundle rebuilt.
- After bootstrap exit, the embedded base Python imported PySide6 6.11.1,
  Qt 6.11.1, IPython 9.17.1 and the local QtADS module directly from
  `python-environment/lib/python3.12/site-packages`. All recorded dependency
  paths are under the fixture environment, and none contains `archive-v0`.
- Changed-source lint, Python compilation and whitespace checks pass.

Python 3.12 was already installed on this host; a fresh Python download was not
needed or claimed as tested. The user checklist and spike README now give the
online first-run command and explicit offline replay. This bootstrap verification
does not advance task 037's remaining physical acceptance obligations. No Pyzo,
binding or user configuration was changed; nothing was pushed.
