"""Fresh-process proof that the live application restores a workspace set.

Run with ``PYZO_WORKSPACE_SET_PHASE=first`` to seed A/B and with ``second``
to restore the same generation. The probe uses the configured launcher and
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
if phase == "first" and not os.path.exists(os.path.join(workspace_dir, "manifest.json")):
    store = WorkspacePersistenceStore(workspace_dir)
    store.commit(
        WorkspacePersistenceState(
            ("workspace-a", "workspace-b"),
            "workspace-a",
            {
                identity: {
                    "schema": 1,
                    "identity": identity,
                    "name": identity.rsplit("-", 1)[-1].upper(),
                    "session": {
                        "schema": 1,
                        "layout": {
                            "schema": 1,
                            "active_pane_id": (
                                "persisted-pane-b"
                                if identity == "workspace-b"
                                else None
                            ),
                            "frames": (
                                [
                                    {
                                        "id": "persisted-frame-b",
                                        "root": {
                                            "type": "group",
                                            "group_id": "persisted-group-b",
                                        },
                                        "groups": [
                                            {
                                                "id": "persisted-group-b",
                                                "panes": ["persisted-pane-b"],
                                                "active_pane_id": "persisted-pane-b",
                                                "tab_side": "top",
                                            }
                                        ],
                                    }
                                ]
                                if identity == "workspace-b"
                                else []
                            ),
                        },
                    },
                    "profile": {},
                    "extensions": {"pyzo_peer_initialized": True},
                }
                for identity in ("workspace-a", "workspace-b")
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
                    }
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

    def inspect():
        identities = tuple(
            sorted(str(identity) for identity in pyzo.application.workspaces.identities)
        )
        expected = ("workspace-a", "workspace-b")
        assert identities == expected, identities
        retained = [
            editor
            for editor in pyzo.editors
            if editor.toPlainText() == "workspace B retained\n"
        ]
        assert len(retained) == 1, retained
        view_id = pyzo.application.documents.view_identity(retained[0])
        assert view_id
        view = pyzo.application.documents.registry.view(view_id)
        assert str(view.workspace_id) == "workspace-b", view.workspace_id
        workspace_b = pyzo.application.workspaces.model(view.workspace_id)
        assert len(workspace_b.serialize_layout()["frames"]) == 1
        assert len(workspace_b.panes) == 1
        print(phase.upper(), "WORKSPACES", " ".join(identities), flush=True)
        pyzo.application.lifecycle.quit()

    pyzo.callLater(inspect)


MainWindow.__init__ = init_and_probe
pyzo._start.start()
