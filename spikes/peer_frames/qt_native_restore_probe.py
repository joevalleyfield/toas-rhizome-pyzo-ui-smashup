"""Minimal process-owned reproduction of a detached QtADS restore target."""

from PySide6 import QtWidgets
from spikes.peer_frames.qtads_backend import QtAdsPeerFrameBackend
from spikes.peer_frames.contract import PaneDescriptor, PaneKind, WorkspaceModel
from copy import deepcopy

app = QtWidgets.QApplication([])
b = QtAdsPeerFrameBackend()
m = WorkspaceModel(b)
b.bind_model(m)
for pane, frame in [("one", "A"), ("two", "B")]:
    assert m.register_pane(PaneDescriptor(pane, PaneKind.CUSTOM, pane)).applied
    assert m.create_frame(pane, frame).applied
saved = deepcopy(m.serialize_layout())
saved["frames"][0]["groups"][0]["panes"] = ["two"]
saved["frames"][0]["groups"][0]["active_pane_id"] = "two"
saved["frames"][1]["id"] = "C"
saved["frames"][1]["groups"][0]["panes"] = ["one"]
saved["frames"][1]["groups"][0]["active_pane_id"] = "one"
original = b.manager.addDockWidgetToContainer


def traced(area, dock, container):
    print(
        "PLACEMENT", dock.objectName(), "manager", container.dockManager(), flush=True
    )
    return original(area, dock, container)


b.manager.addDockWidgetToContainer = traced
print("RESTORE A<-two C<-one", flush=True)
assert m.restore_layout(saved).applied
assert b.capture_layout() == saved
print("NATIVE RESTORE LIFECYCLE COMPLETE", flush=True)
b.close()
app.processEvents()
