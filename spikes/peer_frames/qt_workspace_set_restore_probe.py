"""Fresh-process proof that the live application restores a workspace set.

Run with ``PYZO_WORKSPACE_SET_PHASE=first`` to seed A/B/C with two B views,
``retry`` to inject and recover a failed B runtime, and ``verify`` to restore
the retry's durable generation. ``empty`` seeds an explicitly empty loaded
set. ``close`` unloads A, ``close-empty`` unloads the final B runtime, and
``reopen``/``reopen-empty`` start with B-only/empty loaded sets before
explicitly reloading A. The probe uses
the configured launcher and
offscreen Qt; it never drives the operating-system window manager.
"""

from __future__ import annotations

import os
import sys
import types

from pyzo.util import paths

from spikes.peer_frames.workspace_persistence import (
    WorkspacePersistenceState,
    WorkspacePersistenceStore,
)


probe_dir = os.environ["PYZO_WORKSPACE_SET_PROBE_DIR"]
workspace_dir = os.path.join(probe_dir, "workspaces")
recovery_dir = os.path.join(probe_dir, "recovery")
os.makedirs(probe_dir, exist_ok=True)
os.makedirs(os.path.join(probe_dir, "tools"), exist_ok=True)
os.makedirs(recovery_dir, exist_ok=True)
os.chdir(probe_dir)
paths.prepare_appdata_appconfig_dirs = lambda: (probe_dir, probe_dir)

commandline = types.ModuleType("pyzo.core.commandline")
commandline.is_our_server_running = lambda: False
commandline.handle_cmd_args = lambda: None
commandline.stop_our_server = lambda: None
sys.modules["pyzo.core.commandline"] = commandline

phase = os.environ["PYZO_WORKSPACE_SET_PHASE"]
injected_create = None


def finish_probe():
    """Complete application teardown, then stop this test-owned Qt loop."""

    import threading

    # Arm the test-only deadline before lifecycle negotiation: a broken close
    # path must not be able to prevent the harness from cleaning up its own
    # process.
    threading.Timer(2.0, os._exit, args=(0,)).start()
    pyzo.application.lifecycle.quit()
    from pyzo.qt import QtWidgets

    app = QtWidgets.QApplication.instance()
    if app is not None:
        app.exit(0)


if phase == "retry":
    from pyzo.core.workspaceRuntime import WorkspaceRuntimeCatalog

    injected_create = WorkspaceRuntimeCatalog.create

    def fail_workspace_b(self, **kwargs):
        if str(kwargs.get("identity")) == "workspace-b":
            raise RuntimeError("injected workspace-b construction failure")
        return injected_create(self, **kwargs)

    WorkspaceRuntimeCatalog.create = fail_workspace_b

if phase in {"first", "empty"} and not os.path.exists(
    os.path.join(workspace_dir, "manifest.json")
):
    store = WorkspacePersistenceStore(workspace_dir)
    loaded_workspace_ids = () if phase == "empty" else ("workspace-a", "workspace-b")
    active_workspace_id = None if phase == "empty" else "workspace-a"
    store.commit(
        WorkspacePersistenceState(
            loaded_workspace_ids,
            active_workspace_id,
            {
                identity: {
                    "schema": 1,
                    "identity": identity,
                    "name": identity.rsplit("-", 1)[-1].upper(),
                    "persistence_location": (
                        "/optional/project-a"
                        if identity == "workspace-a"
                        else "/optional/missing-" + identity
                    ),
                    "session": (
                        {
                        "schema": 1,
                        "layout": {
                            "schema": 1,
                            "active_pane_id": (
                                "persisted-pane-b-2"
                                if identity == "workspace-b"
                                else None
                            ),
                            "frames": (
                                [
                                    {
                                        "id": "persisted-frame-b",
                                        "root": {
                                            "type": "group",
                                            "group_id": "persisted-group-b-1",
                                        },
                                        "groups": [
                                            {
                                                "id": "persisted-group-b-1",
                                                "panes": ["persisted-pane-b-1"],
                                                "active_pane_id": "persisted-pane-b-1",
                                                "tab_side": "top",
                                            }
                                        ],
                                    },
                                    {
                                        "id": "persisted-frame-b-2",
                                        "root": {
                                            "type": "group",
                                            "group_id": "persisted-group-b-2",
                                        },
                                        "groups": [
                                            {
                                                "id": "persisted-group-b-2",
                                                "panes": ["persisted-pane-b-2"],
                                                "active_pane_id": "persisted-pane-b-2",
                                                "tab_side": "top",
                                            },
                                        ],
                                    }
                                ]
                                if identity == "workspace-b"
                                else [
                                    {
                                        "id": "persisted-frame-a",
                                        "root": {
                                            "type": "group",
                                            "group_id": "persisted-group-a",
                                        },
                                        "groups": [
                                            {
                                                "id": "persisted-group-a",
                                                "panes": ["persisted-pane-a"],
                                                "active_pane_id": "persisted-pane-a",
                                                "tab_side": "top",
                                            }
                                        ],
                                    }
                                ]
                                if identity == "workspace-a"
                                else []
                            ),
                        },
                        }
                        if identity != "workspace-a"
                        else {}
                    ),
                    "profile": {},
                    "extensions": {"pyzo_peer_initialized": True},
                }
                for identity in ("workspace-a", "workspace-b", "workspace-c")
            },
            {
                "schema": 1,
                "documents": {
                    "document-b": {
                        "path": None,
                        "text": "workspace B retained\n",
                        "clean_text": "workspace B retained\n",
                        "revision": 1,
                        "live": True,
                        "available": True,
                        "undo": [],
                        "redo": [],
                }
            },
                "views": {
                    "view-a": {
                        "document_id": "document-b",
                        "workspace_id": "workspace-a",
                        "state": {
                            "cursor": 6,
                            "selection": (6, 6),
                            "scroll": 0,
                            "focused": False,
                            "pinned": False,
                            "run_highlight": None,
                        },
                        "epoch": 1,
                    },
                    "view-b": {
                        "document_id": "document-b",
                        "workspace_id": "workspace-b",
                        "state": {
                            "cursor": 3,
                            "selection": (3, 3),
                            "scroll": 0,
                            "focused": False,
                            "pinned": False,
                            "run_highlight": None,
                        },
                        "epoch": 1,
                    },
                    "view-b-2": {
                        "document_id": "document-b",
                        "workspace_id": "workspace-b",
                        "state": {
                            "cursor": 10,
                            "selection": (10, 10),
                            "scroll": 4,
                            "focused": False,
                            "pinned": True,
                            "run_highlight": None,
                        },
                        "epoch": 1,
                    },
                },
                "retained_views": {},
                "mains": {},
                "extensions": {},
            },
            {
                identity: {
                    "schema": 1,
                    "workspace_id": identity,
                    "snapshots": [],
                }
                for identity in ("workspace-a", "workspace-b")
            },
            {},
        )
    )

sys.argv = ["pyzolauncher.py"]
import pyzo._start
from pyzo.core.main import MainWindow


original_init = MainWindow.__init__


def init_and_probe(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    pyzo._peer_probe_main_window = self

    def inspect():
        identities = tuple(
            sorted(str(identity) for identity in pyzo.application.workspaces.identities)
        )
        if phase == "empty":
            persisted = WorkspacePersistenceStore(workspace_dir).load()
            assert persisted.state.loaded_workspace_ids == ()
            assert not tuple(pyzo.editors)
            created = pyzo.application.workspaces.create("explicit-new")
            assert created in pyzo.application.workspaces.identities, created
            print("EMPTY WORKSPACES", flush=True)
            finish_probe()
            return
        from spikes.peer_frames.identity import ApplicationIdentity, IdentityKind

        if phase in {"reopen", "reopen-empty"}:
            expected_before = ("workspace-b",) if phase == "reopen" else ()
            assert identities == expected_before, identities
            result = pyzo.application.workspaces.reopen(
                ApplicationIdentity(IdentityKind.WORKSPACE, "workspace-a")
            )
            assert result.applied, result
            identities = tuple(
                sorted(
                    str(identity)
                    for identity in pyzo.application.workspaces.identities
                )
            )
            expected_after = (
                ("workspace-a", "workspace-b")
                if phase == "reopen"
                else ("workspace-a",)
            )
            assert identities == expected_after, identities
            snapshot = pyzo.application.documents.registry.persistence_snapshot()
            a_view_ids = {
                view_id
                for view_id, view in snapshot["views"].items()
                if view.get("workspace_id") == "workspace-a"
            }
            assert len(a_view_ids) == 1, snapshot
            restored_a = [
                editor
                for editor in pyzo.editors
                if str(pyzo.application.documents.view_identity(editor))
                in a_view_ids
            ]
            assert len(restored_a) == 1, restored_a
            if phase == "reopen-empty":
                from pyzo.qt import QtWidgets

                persisted = WorkspacePersistenceStore(workspace_dir).load()
                assert (
                    persisted.state.workspaces["workspace-a"][
                        "persistence_location"
                    ]
                    == "/optional/project-a"
                )
                assert persisted.state.workspaces["workspace-c"][
                    "persistence_location"
                ] == "/optional/missing-workspace-c"
                restored_resource = pyzo.application.documents.resource(
                    restored_a[0]
                )
                assert restored_resource.path is None
                assert restored_a[0].toPlainText() == (
                    "workspace B retained\n!shared!"
                )
                assert restored_resource.text == restored_a[0].toPlainText()
                assert restored_a[0].undo()
                QtWidgets.QApplication.processEvents()
                assert restored_resource.text == "workspace B retained\n!"
                assert restored_a[0].redo()
                QtWidgets.QApplication.processEvents()
                assert restored_resource.text == (
                    "workspace B retained\n!shared!"
                )
            print("REOPEN WORKSPACES", " ".join(identities), flush=True)
            finish_probe()
            return
        if phase == "cancel-close":
            assert identities == ("workspace-a", "workspace-b"), identities
            main_window = pyzo._peer_probe_main_window
            main_window._peerDirtyCloseChooser = (
                lambda _document_id, _lifecycle: "discard"
            )
            main_window._peerShellCloseChooser = (
                lambda _pane_id, _lifecycle: "cancel"
            )
            before = WorkspacePersistenceStore(workspace_dir).load()
            result = pyzo.application.workspaces.close(
                ApplicationIdentity(IdentityKind.WORKSPACE, "workspace-a")
            )
            assert not result.applied, result
            assert tuple(
                sorted(
                    str(identity)
                    for identity in pyzo.application.workspaces.identities
                )
            ) == ("workspace-a", "workspace-b")
            after = WorkspacePersistenceStore(workspace_dir).load()
            assert after.generation == before.generation
            assert after.state.loaded_workspace_ids == (
                "workspace-a",
                "workspace-b",
            )
            print("CANCEL CLOSE", " ".join(identities), flush=True)
            finish_probe()
            return
        if phase in {"close", "close-empty"}:
            expected_before = (
                ("workspace-a", "workspace-b")
                if phase == "close"
                else ("workspace-b",)
            )
            assert identities == expected_before, identities
            main_window = pyzo._peer_probe_main_window
            main_window._peerDirtyCloseChooser = (
                lambda _document_id, _lifecycle: "discard"
            )
            main_window._peerShellCloseChooser = (
                lambda _pane_id, _lifecycle: "terminate"
            )
            target = "workspace-a" if phase == "close" else "workspace-b"
            result = pyzo.application.workspaces.close(
                ApplicationIdentity(IdentityKind.WORKSPACE, target)
            )
            assert result.applied, result
            identities = tuple(
                sorted(
                    str(identity)
                    for identity in pyzo.application.workspaces.identities
                )
            )
            expected_after = ("workspace-b",) if phase == "close" else ()
            assert identities == expected_after, identities
            persisted = WorkspacePersistenceStore(workspace_dir).load()
            assert persisted.state.loaded_workspace_ids == expected_after
            assert "workspace-a" in persisted.state.workspaces
            assert persisted.state.workspaces["workspace-a"][
                "persistence_location"
            ] == "/optional/project-a"
            if phase == "close":
                from pyzo.qt import QtWidgets

                retained = [
                    editor
                    for editor in pyzo.editors
                    if editor.toPlainText().startswith("workspace B retained\n")
                    and str(
                        pyzo.application.documents.registry.view(
                            pyzo.application.documents.view_identity(editor)
                        ).workspace_id
                    )
                    == "workspace-b"
                ]
                assert len(retained) == 2, retained
                primary, peer = retained
                resource = pyzo.application.documents.resource(primary)
                base_text = "workspace B retained\n!"
                latest_text = base_text + "shared!"
                cursor = primary.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                primary.setTextCursor(cursor)
                primary.insertPlainText("shared!")
                QtWidgets.QApplication.processEvents()
                assert resource.text == latest_text, (
                    resource.text,
                    primary.toPlainText(),
                    peer.toPlainText(),
                )
                assert peer.toPlainText() == resource.text, (
                    resource.text,
                    primary.toPlainText(),
                    peer.toPlainText(),
                )
                assert peer.undo()
                QtWidgets.QApplication.processEvents()
                assert resource.text == base_text
                assert primary.redo()
                QtWidgets.QApplication.processEvents()
                assert resource.text == latest_text
                pyzo.workspacePersistence.save()
                persisted = WorkspacePersistenceStore(workspace_dir).load()
                assert (
                    persisted.state.shared_resources["documents"]["document-b"][
                        "text"
                    ]
                    == resource.text
                )
            print("CLOSE WORKSPACES", " ".join(identities), flush=True)
            finish_probe()
            return
        if phase == "retry":
            assert identities == ("workspace-a",), identities
            failures = pyzo.application.workspaces.restore_failures
            print("RETRY FAILURES", repr(failures), flush=True)
            assert failures == {
                "workspace-b": "injected workspace-b construction failure"
            }, failures
            WorkspaceRuntimeCatalog.create = injected_create
            result = pyzo.application.workspaces.retry_restore(
                ApplicationIdentity(IdentityKind.WORKSPACE, "workspace-b")
            )
            assert result.applied, result
            identities = tuple(
                sorted(
                    str(identity)
                    for identity in pyzo.application.workspaces.identities
                )
            )
        expected = ("workspace-a", "workspace-b")
        assert identities == expected, identities
        persisted = WorkspacePersistenceStore(workspace_dir).load()
        assert "workspace-c" in persisted.state.workspaces
        assert "workspace-c" not in identities
        retained = [
            editor
            for editor in pyzo.editors
            if editor.toPlainText().startswith("workspace B retained\n")
            and str(
                pyzo.application.documents.registry.view(
                    pyzo.application.documents.view_identity(editor)
                ).workspace_id
            )
            == "workspace-b"
        ]
        retained.sort(
            key=lambda editor: str(pyzo.application.documents.view_identity(editor))
        )
        assert len(retained) == 2, retained
        view_id = pyzo.application.documents.view_identity(retained[0])
        assert view_id
        view = pyzo.application.documents.registry.view(view_id)
        assert str(view.workspace_id) == "workspace-b", view.workspace_id
        workspace_b = pyzo.application.workspaces.model(view.workspace_id)
        layout = workspace_b.serialize_layout()
        assert len(layout["frames"]) == 2
        assert len(workspace_b.panes) == 2
        positions = sorted(editor.textCursor().position() for editor in retained)
        expected_positions = [3, 10] if phase == "first" else [10, 21]
        assert positions == expected_positions, positions
        from pyzo.qt import QtWidgets

        if phase in {"first", "verify"}:
            primary, peer = retained
            resource = pyzo.application.documents.resource(primary)
            original_text = "workspace B retained\n"
            if phase == "first":
                cursor = primary.textCursor()
                cursor.movePosition(cursor.MoveOperation.End)
                primary.setTextCursor(cursor)
                primary.insertPlainText("!")
                QtWidgets.QApplication.processEvents()
                assert resource.text == original_text + "!", resource.text
                assert peer.toPlainText() == original_text + "!"
                assert peer.textCursor().position() == 10
                assert peer.undo()
                QtWidgets.QApplication.processEvents()
                assert resource.text == original_text
                assert primary.toPlainText() == original_text
                assert peer.toPlainText() == original_text
                assert primary.redo()
                QtWidgets.QApplication.processEvents()
                assert resource.text == original_text + "!"
                assert primary.toPlainText() == original_text + "!"
                assert peer.toPlainText() == original_text + "!"
            else:
                assert resource.text == original_text + "!"
                assert peer.undo()
                QtWidgets.QApplication.processEvents()
                assert resource.text == original_text
                assert primary.toPlainText() == original_text
                assert peer.toPlainText() == original_text
                assert primary.redo()
                QtWidgets.QApplication.processEvents()
                assert resource.text == original_text + "!"
                assert primary.toPlainText() == original_text + "!"
                assert peer.toPlainText() == original_text + "!"
        print(phase.upper(), "WORKSPACES", " ".join(identities), flush=True)
        finish_probe()

    pyzo.callLater(inspect)


MainWindow.__init__ = init_and_probe
pyzo._start.start()
