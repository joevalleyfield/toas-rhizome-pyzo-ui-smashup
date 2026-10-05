# 028: Live workspace cell, File, Main and script routes

## Status

COMPLETE — accepted by Codex 2026-10-05; compiled 2026-10-05 from the existing Stage 4 NEXT gate under “Next.”
Depends on accepted 026/027 (root `a4ff0bf5`, Pyzo `19d619a0`). The September
scope amendment remains normative. This is a bounded continuation of 014.

Accepted root implementation `7859b4fa2f388c49d0801c53b53aa48ec4a19273` and Pyzo
`43a1376ecf3a4447ce93ef78cee5e77bf2e771d5`. See
[completion evidence](../../docs/evidence/workspace-run-variants-2026-10-05.md).

## Outcome

Route cell/advance, Execute File/Main and Run File/Main as Script through the
same invoking-view resolver as Selection. Main belongs to the invoking workspace
and is a retained document reference, independent of its open views. Preserve
buffer/no-save Execute behavior, native autosave failure/cancellation, regular
Python restart and the existing IPython `%cd`/`%run -i` branch. Capture the target
before autosave and revalidate it after any modal save/focus/ownership changes.
The checked Run target chooser must describe all editor execution commands.

## Allowed writes

Pyzo workspaceExecution/runCommands, bounded Main designation/editor-provider
wiring, accurate remaining debugger-target labels, native document file-format retention and Run/editor-menu projection; focused tests; root test-owned real-kernel
probe/harness; task evidence and existing mutable queue references. No debugger,
completion/help/tool callback migration, shell migration, File Move/Fork UX,
QtADS/binding, TOAS/Rhizome changes or portable/sync work.

## Pre-edit state/assertion coverage

| State / order | Executable assertion | Current path / gap |
| --- | --- | --- |
| Cell, cell advance, File, Main, both script variants; implicit/explicit local target; global/foreign focus | `receipt.command == variant`; deliveries only captured local shell; owner/shell/generation match | Selection bridge only; other variants global (gap) |
| Execute dirty/named/untitled; directory setting; cell parser/header/EOF | exact buffer payload, filename/line/cell/changeDir; `saves == restarts == []`; bytes unchanged; advance captured editor only | Existing extraction preserved; new dispatch needed |
| Missing/retired/moved invoker, missing/lost/broken shell, unavailable owner | `sends == saves == restarts == []`; visible refusal; no older/foreign fallback | Shared admission/assignment paths reused |
| Independent A/B mains, shared resource, closed main view, rename, missing/unavailable/pathless main | correct workspace resource/text/path; missing/unavailable refuse with zero sends; designation identity survives save/close | Registry main supports; global scan/UI wiring gap |
| Native view bind / retained reopen / application restore | current registry main identity stays unchanged on binding; legacy main flag consumed only during initial migration; native saved-byte baseline projects on restore | Cached main replay at bind can overwrite live designation (gap) |
| Main designation pathless save succeeds/fails/cancels; view changes during save | designation only captured live owner/document; no failed mutation; local checked marker | Existing tabs string designation bypasses registry (gap) |
| Script save succeeds, fails/cancels or remains dirty | save exactly selected document; success restart(path) only selected Python shell; failed/dirty zero sends/restarts | Legacy native saver retained; peer guard gap |
| Save changes focus/global target, explicit target, owner/view lifetime, kernel generation or main designation | focus-only preserves captured route; effective route/owner/generation/main change gives zero restart/send | Post-save revalidation gap |
| Save As changes path on same document; normal trailing-whitespace save edits | captured document retained; final saved path used; clean saved content executes | Native save behavior preserved |
| Closed Main as Script | resolves first, obtains same-workspace native view for existing saver; saved retained text executes; no foreign main fallback | Native editor provider gap; script may reopen retained main view |
| Closed Main native save format / external disk change | BOM/newlines and last clean byte baseline preserved; changed disk still invokes existing overwrite/cancel path; canceled native save leaves retained clean baseline unchanged | Native view reopen needs baseline/format projection; EditorTabs currently adopts a canceled native save (gap) |
| File-format snapshot / stale shared native baseline / explicit document forget | saved baseline survives stale view snapshot; `format_keys <= document_ids`; forgotten entry removed | New native file-format metadata lifecycle uses existing save/snapshot/forget boundary |
| Python restart pending/completed/failed; IPython script branch | same shell ID/new generation after successful Python restart; old result rejected; IPython exact two commands/no restart | Existing native restart and bridge generation guard; branch preserved |
| Focus changes during cell dispatch; stale dispatch | only captured editor advances on successful send; no history/advance/send on refusal | Cell relooks up editor (gap) |
| Legacy, ordinary Run/debug/postmortem/multi-kernel, retention | compatibility controls pass; peer controls use new local route | Existing full controls required |

These assertions map the pre-edit decision states to existing paths or explicit
gaps. User “Next” authorizes the gate and its necessary fixes/checks; no strict
external-validation mode is requested. No new priority or global objective.

## Acceptance

Focused route/payload/save/main/epoch tests; test-owned Qt app with A/B actual
kernels exercising all variants, retained Main and real save/restart; full peer
and legacy controls plus coordinated suite. Record exact revisions, before/after
failures, test counts, source writes limited to explicit script save, cleanup and
limits. Commit accepted implementation before moving NEXT to the already-planned
native request/result provenance gate. Full Stage 4 remains pending.


## Completion

All remaining editor Run variants use the invoking view's local resolver and
assignment. Retained workspace Main references, pathless designation save,
closed-Main execution, native file format/clean-baseline projection and canceled
native save correction are implemented. Script revalidates after autosave;
regular Python restarts the selected shell and IPython preserves `%run -i`.
The chooser covers every editor command; the peer compatibility target label
accurately describes remaining debugger selection.

Coordinated verification: **420 passed, 13 skipped, 45 subtests**, 2.36s.
**12 live controls passed**, 40.67s; new actual-kernel Run probe 5.742s.
Full peer **11.105s**, legacy **7.309s**. Compilation, name/import and whitespace
checks pass. The implementation commits precede movement of NEXT. Root/Pyzo
completion cleanup and full logs are recorded in the evidence artifact.

Full Stage 4 remains pending native request/result provenance. September deferrals,
Stage 5/6 ownership work, separate File Move/Fork UX and native platform-validation
limits remain unchanged. Binding and TOAS/Rhizome changes were not made; nothing
was pushed.
