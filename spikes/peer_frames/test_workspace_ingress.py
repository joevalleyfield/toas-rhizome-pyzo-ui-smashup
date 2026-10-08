"""Ingress ownership is independent of editor/path and native focus pointers."""

from itertools import permutations, product

import pytest

from spikes.peer_frames.contract import PaneDescriptor, PaneKind, WorkspaceModel
from spikes.peer_frames.fake_backend import FakeBackend
from spikes.peer_frames.workspace_coordinator import WorkspaceCoordinator


@pytest.mark.parametrize("order", list(permutations(range(3))))
@pytest.mark.parametrize("available", list(product((False, True), repeat=3)))
def test_ingress_mru_and_every_eligibility_combination(order, available):
    coordinator = WorkspaceCoordinator()
    owners = [
        coordinator.add_workspace(WorkspaceModel(FakeBackend()), name=str(index))
        for index in range(3)
    ]
    for index in order:
        coordinator.activate_workspace(owners[index])
        coordinator.activate_workspace(owners[index])
    expected = next((owners[i] for i in reversed(order) if available[i]), None)
    assert (
        coordinator.external_open_workspace(
            lambda owner: available[owners.index(owner)]
        )
        == expected
    )


@pytest.mark.parametrize("activation", ["workspace", "pane", "backend"])
def test_every_foreground_entry_updates_history_and_removal_prunes_it(activation):
    coordinator = WorkspaceCoordinator()
    owners = [
        coordinator.add_workspace(WorkspaceModel(FakeBackend()), name=name)
        for name in ("A", "B", "C")
    ]
    for owner in owners[:2]:
        pane = str(owner)
        coordinator.register_pane(owner, PaneDescriptor(pane, PaneKind.TOOL, pane))
        coordinator.model(owner).create_frame(pane)
    for owner in reversed(owners[:2]):
        if activation == "workspace":
            coordinator.activate_workspace(owner)
        elif activation == "pane":
            coordinator.activate_pane(owner, str(owner))
        else:
            coordinator.adopt_backend_activation(owner, str(owner))
    assert coordinator.external_open_workspace(lambda _: True) == owners[0]
    # A closing model cannot be selected even when the application predicate
    # considers it usable. B remains next in foreground order.
    coordinator.model(owners[0]).shutdown_requested = True
    assert coordinator.external_open_workspace(lambda _: True) == owners[1]
    coordinator.model(owners[1]).release_pane(str(owners[1]))
    assert coordinator.remove_workspace(owners[1]).applied
    assert coordinator.external_open_workspace(lambda _: True) == owners[2]
    assert not coordinator.activate_workspace(owners[1]).applied
    assert coordinator.external_open_workspace(lambda _: True) == owners[2]


def test_empty_loaded_set_and_bootstrap_never_route_to_scaffolding():
    coordinator = WorkspaceCoordinator()
    assert coordinator.external_open_workspace(lambda _: True) is None
    owner = coordinator.add_workspace(
        WorkspaceModel(FakeBackend()), name="Bootstrap", persisted=False
    )
    coordinator.activate_workspace(owner)
    assert coordinator.external_open_workspace(lambda _: True) is None
    loaded = coordinator.add_workspace(WorkspaceModel(FakeBackend()), name="Loaded")
    assert coordinator.external_open_workspace(lambda _: True) == loaded
