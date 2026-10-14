"""Dispose a committed Qt window before Windows CRT exec unloads its DLLs."""


def closed_window_exec_hook(window_provider, is_valid, delete):
    """Return an audit hook; the caller limits installation to Windows controls.

    The real os.exec call retains its path, arguments and successor behavior.
    A close cancellation must never dispose the window.
    """
    def before_exec(event, args):
        if event != "os.exec":
            return
        window = window_provider()
        if window is None or not is_valid(window):
            raise RuntimeError("exec requested without a live compatibility window")
        if not window._closeflag or window.isVisible():
            raise RuntimeError("exec requested before compatibility close committed")
        delete(window)
        if is_valid(window):
            raise RuntimeError("compatibility window survived pre-exec cleanup")

    return before_exec
