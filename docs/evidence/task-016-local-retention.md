# Task 016 local retention evidence

Date: 2026-09-07

## Delivered boundary

The existing checksummed generation store now conservatively imports legacy
workspace recovery records during `migrate_legacy`:

- equal candidates for one document coalesce into an application-owned
  `shared_resources.retained_documents` candidate while every source record
  and workspace provenance remains inspectable;
- divergent candidates are preserved in the lossless legacy migration record
  and produce an `ambiguous-recovery` issue requiring explicit selection;
- malformed candidates are preserved in the backed-up/lossless legacy input
  and produce a `malformed-recovery` issue rather than being selected or
  discarded;
- only recovery belonging to the migrated default workspace is installed in
  the active workspace recovery map; candidates from other legacy workspace
  identities remain preserved in migration application state until explicit
  workspace reconciliation;
- retry remains safe because the legacy backup is written before publication,
  and an existing manifest makes repeated migration a no-op.

The existing generation format continues to round-trip document-resource
text, clean baseline, undo/redo lists, view/retained-view descriptors,
workspace catalog entries, and zero-open workspace state. Publication remains
atomic and checksummed; migration does not open or write source-file paths.

## State assertions

- Equal candidates yield one shared retained candidate and preserve all input records.
- Divergent candidates yield no selected shared candidate and an `ambiguous-recovery` issue.
- Malformed candidates yield a `malformed-recovery` issue while valid siblings remain available.
- Existing manifest, interrupted publication, and repeated migration preserve the prior generation and one legacy backup.
- Workspace records outside the loaded set remain in the durable catalog.

## Verification

- Focused persistence suite: **13 tests, OK**.
- Persistence/recovery/document/lifecycle subset: **48 tests, OK**.
- Python 3.12 compilation: **passed**.
- `git diff --check`: **passed**.
- Full root discovery reached Qt-backed tests but exited 134 because this environment lacks the Qt `offscreen` platform plugin.

## Scope and handback

Changed only the allowed persistence module, matching tests, package exports,
task status, and this evidence. No Pyzo source or source files were written.
Task 017 is now eligible under the batch dependency chain.

## Correction pass

Persisted migration issues are rehydrated into every later `load()` result.
Documents with divergent or malformed candidates are blocked from ordinary
active recovery until explicit selection, while raw legacy input and valid
unrelated candidates remain preserved. Candidate validation rejects invalid
text, clean baselines, histories, and workspace snapshot lists without
preventing sibling workspaces from migrating.
