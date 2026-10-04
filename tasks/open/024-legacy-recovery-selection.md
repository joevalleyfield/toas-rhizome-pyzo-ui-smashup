# 024: Explicit legacy recovery selection

## Status

COMPLETE — owner Codex; accepted 2026-10-04. Dependency: accepted focus
correction in Pyzo `e7274793` and current 023 review. User authorized continuing
the next steps and cleanup under the September scope amendment.

## Outcome and writes

Complete the migration gate with an explicit user choice, preserving original
legacy inputs and all divergent candidates. Allowed: root
`workspace_persistence.py`, `document_resources.py` and matching tests;
Pyzo `main.py`, `applicationController.py`, `editorGroups.py`, `menu.py` and
focused tests; isolated real-app migration probe and evidence/roadmap updates.
No new storage engine, source-file writes, shell migration or synchronization.

## Pre-edit state/assertion gate

Selection input: unknown document, already resolved, malformed-only,
out-of-range/non-integer candidate, path collision, missing workspace, valid
named or untitled candidate. Timing: cancel before selection, pending ordinary
retention, successful publication, failed publication, restart after success.
Other resources may be healthy, suspended, or closed. Ordinary file opening
may match an unresolved source (including an alias), or be unrelated.

Assertions: failed/cancelled selection leaves generation, documents and raw
candidates unchanged; success retains selected identity/text/baseline/history
and candidate metadata, all alternatives/raw input survive; no source bytes
change; restart recovers the selected buffer and clears only that document's
blocking issues. A path collision or existing authority cannot be overwritten.
An unresolved file open returns no editable view until explicit selection;
unrelated files remain usable. Durable publication precedes live adoption.

## Acceptance

- Store selection validates the complete proposed resource snapshot before
  atomic publication and rejects invalid/colliding input transactionally.
- File-menu recovery command exposes candidates and cancellation. Ordinary
  file-open guard prompts for matching unresolved records before creating a view.
- Live registry adopts only the new retained document/view; existing bindings
  and shared history remain intact.
- Separate-process real-editor proof covers cancel, publication failure/retry,
  named/untitled selection, restart, Undo/Redo, and unchanged source bytes.
- Re-run regression/retention and relevant application compatibility controls;
  record exact revisions, limits and the renewed integration decision.

## Completion evidence

Explicit preview/selection, ordinary-open guard, transactional store validation,
live adoption and selected closed-buffer reopening are implemented. Six focused
store/registry controls pass; real-app selection/restart checks cancellation,
publication failure/retry, named/untitled history, BOM/CRLF, preserved alternatives,
unrelated bindings, secondary workspace ownership and unchanged source bytes.
Pending ordinary edits are checkpointed before the independent selection
transaction; cancellation itself performs no write. Integration corrections
are documented in 025. Final suites, dependency runtime, logs, commit IDs and
bounded acceptance are recorded in the
[current review](../../docs/evidence/retention-integration-2026-10-04.md).
