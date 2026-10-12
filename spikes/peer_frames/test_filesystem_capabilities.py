"""Unavailable optional permissions must not hide other filesystem errors."""

from types import SimpleNamespace

import pytest

from spikes.peer_frames import filesystem_capabilities as capability


@pytest.mark.parametrize("platform,code,optional", [("nt", 1314, True), ("nt", 5, False), ("posix", 1314, False)])
def test_only_windows_symlink_privilege_is_optional(monkeypatch, platform, code, optional):
    monkeypatch.setattr(capability, "os", SimpleNamespace(name=platform))
    error = OSError("creation refused")
    error.winerror = code

    def refuse(target):
        raise error

    alias = SimpleNamespace(symlink_to=refuse)
    if optional:
        assert capability.create_optional_symlink(alias, "target") is False
    else:
        with pytest.raises(OSError) as caught:
            capability.create_optional_symlink(alias, "target")
        assert caught.value is error


def test_available_symlink_is_exercised(tmp_path):
    target = tmp_path / "target"
    target.write_text("source")
    alias = tmp_path / "alias"
    if not capability.create_optional_symlink(alias, target):
        pytest.skip("optional symlink affordance unavailable to this Windows account")
    assert alias.is_symlink() and alias.read_text() == "source"
