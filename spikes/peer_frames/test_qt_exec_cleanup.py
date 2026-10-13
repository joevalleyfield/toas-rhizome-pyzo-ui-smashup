from types import SimpleNamespace as NS

import pytest

from spikes.peer_frames.qt_exec_cleanup import closed_window_exec_hook


def test_exec_cleanup_requires_committed_close_and_preserves_exec_arguments():
    window = NS(_closeflag=False, isVisible=lambda: False)
    valid = [True]
    calls = []
    def delete(value):
        calls.append(value)
        valid[0] = False
    hook = closed_window_exec_hook(lambda: window, lambda _: valid[0], delete)
    args = ("python.exe", ["python.exe", "profile.py"], None)
    hook("os.spawn", args)
    assert calls == []
    with pytest.raises(RuntimeError, match="close committed"):
        hook("os.exec", args)
    assert calls == [] and valid[0]
    window._closeflag = True
    window.isVisible = lambda: True
    with pytest.raises(RuntimeError, match="close committed"):
        hook("os.exec", args)
    assert calls == []
    window.isVisible = lambda: False
    hook("os.exec", args)
    assert calls == [window] and not valid[0]
    assert args == ("python.exe", ["python.exe", "profile.py"], None)


def test_exec_cleanup_does_not_accept_missing_or_failed_disposal():
    hook = closed_window_exec_hook(lambda: None, lambda _: True, lambda _: None)
    with pytest.raises(RuntimeError, match="live compatibility window"):
        hook("os.exec", ())
    window = NS(_closeflag=True, isVisible=lambda: False)
    hook = closed_window_exec_hook(lambda: window, lambda _: True, lambda _: None)
    with pytest.raises(RuntimeError, match="survived pre-exec cleanup"):
        hook("os.exec", ())
