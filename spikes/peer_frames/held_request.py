"""Helpers for delaying one native request callback in live acceptance probes."""

from __future__ import annotations

import time


def outstanding_requests(shell):
    """Return not-yet-done requests on a shell's Yoton request channel."""
    return tuple(
        future
        for future in shell._request._request_items.values()
        if not future.done()
    )


class Held:
    def __init__(self, future, method):
        self.future, self.method, self.callbacks = future, method, []
        self.started = time.monotonic()

    def add_done_callback(self, callback):
        self.callbacks.append(callback)

    def __getattr__(self, name):
        return getattr(self.future, name)

    def release(self):
        try:
            successful = self.future.done() and not self.future.exception()
        except Exception:
            first_send_time = getattr(self.future, "_first_send_time", None)
            print(
                "HELD REQUEST FAILURE",
                {
                    "method": self.method,
                    "held_elapsed_seconds": round(
                        time.monotonic() - self.started, 3
                    ),
                    "future_age_seconds": round(
                        time.time() - first_send_time, 3
                    ) if first_send_time is not None else None,
                    "status": getattr(self.future, "_status", None),
                    "cancelled": self.future.cancelled(),
                    "auto_cancel_timeout": getattr(
                        self.future, "_auto_cancel_timeout", None
                    ),
                },
                flush=True,
            )
            raise
        assert successful
        for callback in self.callbacks:
            callback(self)


def hold_one_request(shell, trigger):
    """Hold only the evalMultiple request synchronously issued by trigger."""
    request = shell._request
    name = "requestWithProvenance"
    had_instance_override = name in request.__dict__
    instance_override = request.__dict__.get(name)
    original = getattr(request, name)
    held = []

    def send(*args):
        method = args[2]
        assert method == "evalMultiple", method
        future = Held(original(*args), method)
        held.append(future)
        return future

    setattr(request, name, send)
    try:
        trigger()
    finally:
        if had_instance_override:
            setattr(request, name, instance_override)
        else:
            delattr(request, name)
    assert (name in request.__dict__) is had_instance_override
    assert len(held) == 1, len(held)
    return held[0]
