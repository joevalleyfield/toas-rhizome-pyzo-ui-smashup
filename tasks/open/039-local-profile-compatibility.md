# Local upstream, legacy QtADS and peer profile compatibility

## Status

DONE by Codex, 2026-10-10, under task 014 Stage 7 and the user's
“See how it goes” authorization to start the local compatibility pass.

## Scope and acceptance

Use the pristine upstream baseline 26c2c32778dddf8fca3c1a44112941b22f075264
from the local Pyzo repository, the current fork's legacy QtADS mode, and peer
mode with fresh test-owned profiles. Exercise real kernels, editor state,
configuration/tools, Cancel, real process Restart and Quit. Migrate profiles
created by both controls into peer mode, restart them, and check compatibility
when reopening the same profile in its originating control. Assert that source
files never change during migration/restart. Keep command servers, configuration
and recovery isolated. Replay existing integrated local controls after any fix.

Allowed writes: root spike probes/tests, local task/evidence/checklist, temporary
fixtures; bounded demonstrated Pyzo fixes under task 014's state assertion gate.
Do not modify the pristine control, bindings or the user's profile. This slice
does not accept native Windows/Linux or unperformed physical macOS cases.

## Planned assertion coverage

| State | Machine check |
| --- | --- |
| Fresh upstream / legacy / peer | expected QMainWindow presence/absence; real shell reaches Ready |
| Saved files, main/pinned, cursor, tools and unknown config | seed through live editors; compare restored values and file bytes |
| Cancel with dirty editor / live peer shell | no exit, editor text and shell connection survive; no disk write |
| Actual Restart / subsequent Quit | successor PID unchanged by exec, phase advances; markers and nonzero failures enforced externally |
| Control profile to peer, then peer restart | no duplicate file views; metadata/config survive; persisted migration archive exists |
| Migrated profile reopened in originating control | legacy state/config remains readable; peer manifest is unchanged by control |
| Timeout / assertion / Qt callback failure | owned process-group deadline; explicit failing exit; never infer success from exit alone |

## Completion evidence

Accepted local checks: four real compatibility controls (including negative
callback failure), 701 coordinated tests/351 subtests, all 22 existing integrated
live controls, Python 3.12 compilation, scoped lint and whitespace. The exact
online user replay command also passes. [Evidence and replay steps](../../docs/evidence/profile-compatibility-2026-10-10.md)
record six bounded repairs and retained failure logs. Accepted Pyzo revision:
`c956237aa6cf53a0cea21b286d8ee6518d814d8c`. Root implementation:
`93be43e502dddedcc6ba2fc448737bbfa3d431c9`. Bindings and user profiles unchanged;
nothing pushed. This local
slice does not accept the complete Stage 7 requirement/platform matrix.

## Migration repair gate

Observed: both pristine and legacy controls preserve two open files, main/pin,
cursor, tools and config through actual exec Restart and a second launch. Both
then enter peer startup with no named editors. `_peerFactoryStartup` selects
`newFile()` instead of legacy restoration whenever no peer layout exists, even
when `state.editorState2` and `state.loadedTools` contain real user state.

| State | Path and assertion | Before |
| --- | --- | --- |
| No legacy files/tools, no peer layout | factory startup; fresh editor/default tools, real Ready shell | covered by fresh peer control |
| Legacy files only / tools only / both; first migration or interrupted migration retry | legacy restore/default-frame path; named views equal surviving legacy files and configured tools are present | uncovered bug: factory skips both |
| Legacy file missing or empty tool list | existing restore skips missing path, ensures usable empty editor/default tools | existing restore contract |
| Modern documents/views or initialized owner, layout present | modern authority wins; legacy restoration guard refuses duplicate disk reads | existing restart controls |
| Modern authority, no layout, stale legacy file/tool list | existing modern guard still wins; default frame uses configured tools | covered by guard + restart controls |
| Persisted empty set / unavailable requested set / blocked persistence | keep existing empty/unavailable branches; no fabrication | existing retention controls |
| `--test` smoke | keep test-mode factory suppression | existing full startup smoke |

Minimal change: a factory layout is eligible only if the compatibility profile
has neither an editor-state list nor a loaded-tool list. No persistence schema,
default placement, migration archive or modern-authority guard changes. The
user's standing carte-blanche and current execution request authorize this
demonstrated repair. Assertions are the three real profile matrix controls and
the existing empty/unavailable, restore, kernel and full startup controls.

The repaired startup now restores both named files, exposing a second import
gap: `_setCurrentOpenFilesAsSsdfList` writes the main marker into `self._tabs`,
although contextual `loadFile` puts the editor in another host. The subsequent
binding consumes markers only from the editor's actual host, losing the main.
States: same host (legacy/uncontextual), new local host (peer import), an already
open local file (history/deduplication), missing file (existing skip), modern
authority (legacy import guard), retirement (not admitted at this synchronous
startup boundary). Assertion: `getMainEditor().filename == expected_main` after
import and restart; history selection addresses `_group_for_editor(item.editor)`.
Same-host behavior must stay identical. Minimal repair resolves the item's real
group before applying its main marker or history selection. The real matrix
fails the main assertion for both origins and covers the same-host controls.

The fresh-peer Restart stack identifies a third gap: after peer application
shutdown commits, legacy `EditorTabs.closeFile` opens a pinned-file dialog.
Peer pin policy already refuses pane/frame closure and explicitly permits
application shutdown; asking again after retirement cannot roll back safely.
State coverage: legacy/uncommitted clean and dirty closes retain old prompts;
peer pane/frame pin refusal remains in `DocumentViewRegistry`; committed peer
clean retained close must emit no prompt; unexpectedly dirty committed close
must assert before mutation; Cancel/persistence failure never reaches commit.
Assertions: real pinned Restart/Quit completes; a focused close test forbids
both dialog functions in committed clean state and verifies dirty refusal;
default legacy pin Cancel preserves the item. Minimal explicit internal
`_peer_committed` flag is passed only by `_closeCommittedPeerEditor`, through
the group manager, to the editor host. It does not change pin negotiation or
allow an unnegotiated close.

With postcommit prompting removed, all three origins reach the next process.
That process loses pinned state: `_restorePersistedPeerEditors` restores cursor,
selection and scroll from the retained view but never assigns `FileItem._pinned`.
States: retained pinned=True/False (must match), older state missing pin (False),
invalid state (existing store validation/refusal), closed retained view included
on explicit reopen (same descriptor authority), absent view (unchanged skip),
different owner (already indexed by view.workspace_id). Assertion: live item's
pin equals the stored descriptor after restore and controls remain byte-identical.
The matrix fails exactly this assertion for fresh peer and both migrations.
Repair adds the missing bool assignment alongside cursor/scroll restoration;
the existing serializer and default False remain unchanged.

Next-process checks distinguish two write gaps from native reconstruction:
(1) Pin/Unpin only mutates the FileItem, leaving the live registry descriptor
unchanged; (2) peer teardown's `saveEditorState` overwrites compatibility
`editorState2` with the now-empty host set, so originating controls reopen no
files. States for pin writes: live bound peer view (update that exact view),
unbound/legacy item (old local behavior), independent views of a shared document
(no foreign pin changes), late/retired menu (existing menu admission guards).
States for editor config save: legacy (serialize current list), peer (retain
legacy archive; contextual find state and modern registry still save), empty
manager (existing no-op), failed/Cancelled close (no committed teardown).
Assertions: a real context-menu Pin action survives fresh peer Restart;
originating control restores its pre-migration file list; peer persistence
digest is unchanged by fallback. Minimal changes synchronize the menu's one
bound view and stop exporting peer lists into the legacy compatibility slot.
