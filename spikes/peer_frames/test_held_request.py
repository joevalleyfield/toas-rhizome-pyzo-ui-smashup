"""Regression for the stale-reply probe's scoped request interception."""

import unittest

from spikes.peer_frames.held_request import Held, hold_one_request


class Cancelled(Exception):
    pass


class FakeFuture:
    def __init__(self, cancelled=False):
        self._status = 2 if cancelled else 4
        self._auto_cancel_timeout = 0.5

    def done(self):
        return True

    def cancelled(self):
        return self._status == 2

    def exception(self):
        if self.cancelled():
            raise Cancelled("request was cancelled")
        return None


class DynamicRequest:
    """Match ReqChannel's dynamic proxy and return queued fake replies."""

    def __init__(self, *futures):
        self.futures = list(futures)
        self.methods = []

    def __getattr__(self, name):
        def proxy(*args):
            self.methods.append((name, args[2]))
            return self.futures.pop(0)

        return proxy


class Shell:
    def __init__(self, *futures):
        self._request = DynamicRequest(*futures)


def hold_interval(shell, trigger):
    """The old behavior: leave the request spy active after trigger returns."""
    request = shell._request
    original = request.requestWithProvenance
    held = []

    def send(*args):
        result = Held(original(*args), args[2])
        held.append(result)
        return result

    request.requestWithProvenance = send
    trigger()
    return held, original


class HeldRequestTests(unittest.TestCase):
    def test_interval_wide_hold_turns_later_cancelled_request_into_failure(self):
        shell = Shell(FakeFuture(), FakeFuture(cancelled=True))
        captured, original = hold_interval(
            shell,
            lambda: shell._request.requestWithProvenance(
                {}, "epoch", "evalMultiple", []
            ),
        )
        shell._request.requestWithProvenance({}, "epoch", "help", [])
        shell._request.requestWithProvenance = original

        self.assertEqual(len(captured), 2)
        with self.assertRaises(Cancelled):
            captured[1].release()

    def test_scoped_hold_releases_only_target_and_keeps_target_cancellation_fatal(self):
        shell = Shell(FakeFuture(), FakeFuture(cancelled=True))
        callbacks = []
        held = hold_one_request(
            shell,
            lambda: shell._request.requestWithProvenance(
                {}, "epoch", "evalMultiple", []
            ),
        )
        held.add_done_callback(lambda reply: callbacks.append(reply))

        # The hook has been removed, so a later canceled request is independent.
        later = shell._request.requestWithProvenance({}, "epoch", "help", [])
        self.assertTrue(later.cancelled())
        self.assertEqual(shell._request.methods, [
            ("requestWithProvenance", "evalMultiple"),
            ("requestWithProvenance", "help"),
        ])
        held.release()
        self.assertEqual(callbacks, [held])

        cancelled_shell = Shell(FakeFuture(cancelled=True))
        cancelled = hold_one_request(
            cancelled_shell,
            lambda: cancelled_shell._request.requestWithProvenance(
                {}, "epoch", "evalMultiple", []
            ),
        )
        with self.assertRaises(Cancelled):
            cancelled.release()


if __name__ == "__main__":
    unittest.main()
