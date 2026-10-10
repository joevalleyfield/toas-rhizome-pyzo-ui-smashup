# Repeat the physical macOS workspace acceptance

Run from `/Users/tim/Documents/Projects/toas-rhizome-pyzo-ui-smashup` on an
unlocked Mac. This creates a disposable Cocoa application with separate
configuration, persistence, recovery, two workspaces and real Python kernels.
It requires the pinned local QtADS wheel and Xcode command-line compiler.
The first run downloads Python 3.12 and the accepted dependency versions as
needed; no cache-warming ceremony is required. It does not replace your normal
Pyzo application.

1. Build a fresh fixture:

   ```sh
   ./.codex-local/bin/uvt run --python 3.12 python spikes/peer_frames/physical_macos_acceptance.py
   ```

   Keep the printed `directory`. In Finder choose Go → Go to Folder, paste that
   directory and double-click **Pyzo Physical Acceptance.app**. Wait for
   **Physical A** and **Physical B** and both Python prompts. Reopening that
   bundle restores its existing fixture; rerunning without `--directory`
   creates a new one. Quit through the UI before rebuilding an existing bundle.
   Dependencies are installed into `python-environment` within that fixture,
   so the bundle does not depend on uv's internal cache layout.

   Once setup succeeds, you can explicitly prohibit downloads when rebuilding:

   ```sh
   ./.codex-local/bin/uvt run --offline --python 3.12 python spikes/peer_frames/physical_macos_acceptance.py --offline --directory /absolute/path/to/the/fixture
   ```

   Offline setup requires the dependencies to be installed or cached. If it
   fails, retry the first command without offline mode. `--cache-dir /path`
   overrides the dependency cache used by the launcher if needed.

2. In A's local editor add `physical_a_only = 101`; in B's local editor add
   `physical_b_only = 202`. Each edit must appear only in its owner's local
   document. Dock captions must include the right owner and dirty marker.
   Switch owners repeatedly and use File → New: only the foreground owner's
   editor count may increase.

3. Edit `shared.py` in B, then press Command-Z. Both owners must show the same
   edit and undo, with separate cursor positions. Execute
   `print("physical_b_kernel")` in B's shell; only B's shell may show the result.
   File → Open `ingress.py` in B, then A. Each must get its own editor view of
   the same canonical document. Cancel an Open dialog and confirm no new view.

4. Physically drag an editor tab to another tab group, a split docking target,
   outside to float, and back to re-dock within its owner. Text, editor identity,
   shell generation and owner must survive. Try dragging a pane/group onto the
   other owner's window: ownership must not silently transfer. Repeat on top,
   bottom and side tab rails and with another window in front.

5. In Finder use Open With → Other to choose this fixture bundle for
   `ingress.py`, while B is the most recently foregrounded owner; do not change
   the default association. Repeat for A. Check `events.jsonl` for a real
   `file-open` receipt and the matching owner in `snapshot.json`. Also drag the
   file from Finder onto each editor. These are separate OS-delivery and drop
   checks; File → Open alone does not establish them.

6. Close a live shell's native frame and choose Cancel. Its kernel, views and
   layout must survive. Repeat and confirm termination: only that shell/frame
   may close; the other owner must remain intact. Close one shared editor view
   and verify the other owner's view and document remain. Include dirty local
   editors and mixed tool/editor/shell frames.

7. Press Command-Q and Cancel the interpreter prompt. All live objects and
   content must survive. Quit again and confirm. Reopen the same bundle:
   workspace, document and view identities, unsaved text, retained topology,
   owner captions and surviving frame geometry must match. Old shell sessions
   are ephemeral; a fresh default interpreter is expected, not revival of
   every old shell. Repeat using File → Restart with B foreground.

8. Finally exercise application activation after closing all visible frames,
   plus direct keyboard menu/tab traversal. Record what recreates an eligible
   frame. Quit the fixture and keep its `snapshot.json`, `events.jsonl`,
   `process.log` and `workspaces` directory as evidence.

The 2026-10-09 assistant run completed native typing/shared undo, B shell
execution, File dialog ownership, float, single-view close, shell-frame Cancel,
Quit Cancel/confirm, real Restart and fresh relaunch. Step 4's split/re-dock and
cross-owner refusal, step 5's OS/drop delivery, step 6's confirmed individual
live-shell close and step 8's zero-frame activation/full keyboard traversal
still need physical acceptance. The computer-control drag endpoint was
unreliable and once placed a float outside the screen; that view was closed
through its native close button. Do these remaining gestures by hand.

[Detailed evidence](evidence/physical-macos-2026-10-09.md) distinguishes the
observed native results from automated controls and fixture setup.
