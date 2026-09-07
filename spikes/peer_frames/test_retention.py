import unittest

from spikes.peer_frames.retention import RetentionCoordinator, RetentionStatus


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class FakeScheduler:
    def __init__(self, clock):
        self.clock = clock
        self.callbacks = []

    def schedule(self, delay, callback):
        self.callbacks.append((self.clock.now + delay, callback))

    def run_due(self):
        ready = [item for item in self.callbacks if item[0] <= self.clock.now]
        self.callbacks = [item for item in self.callbacks if item[0] > self.clock.now]
        for _when, callback in ready:
            callback()


class FakeWriter:
    def __init__(self):
        self.calls = []

    def __call__(self, snapshot, complete):
        self.calls.append((snapshot, complete))


class RetentionCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.scheduler = FakeScheduler(self.clock)
        self.writer = FakeWriter()
        self.current = {"text": "one"}
        self.coordinator = RetentionCoordinator(
            clock=self.clock,
            capture=lambda: dict(self.current),
            writer=self.writer,
            schedule=self.scheduler.schedule,
        )

    def test_deadline_is_from_first_edit_and_sustained_edits_coalesce(self):
        self.coordinator.edit(1)
        self.clock.now = 0.8
        self.current["text"] = "two"
        self.coordinator.edit(2)
        self.assertEqual(self.coordinator.state.status, RetentionStatus.PENDING)
        self.clock.now = 1.0
        self.scheduler.run_due()
        self.assertEqual([call[0]["text"] for call in self.writer.calls], ["two"])

    def test_idle_and_unchanged_edits_do_not_write_redundantly(self):
        self.assertTrue(self.coordinator.flush())
        self.assertEqual(self.writer.calls, [])
        self.coordinator.edit(1)
        self.clock.now = 1.0
        self.scheduler.run_due()
        self.writer.calls[0][1](1, None)
        self.current["text"] = "one"
        self.coordinator.edit(2)
        self.assertEqual(len(self.writer.calls), 1)

    def test_edit_during_write_stays_pending_until_its_generation_completes(self):
        self.coordinator.edit(1)
        self.clock.now = 1.0
        self.scheduler.run_due()
        self.current["text"] = "two"
        self.coordinator.edit(2)
        self.writer.calls[0][1](1, None)
        self.assertEqual(self.coordinator.state.status, RetentionStatus.PENDING)
        self.assertFalse(self.coordinator.flush())
        self.assertEqual(len(self.writer.calls), 2)
        self.writer.calls[1][1](2, None)
        self.assertEqual(self.coordinator.state.status, RetentionStatus.DURABLE)
        self.assertEqual(self.coordinator.state.durable_revision, 2)

    def test_failure_is_visible_and_retryable(self):
        self.coordinator.edit(1)
        self.assertTrue(self.coordinator.flush() is False)
        error = RuntimeError("disk full")
        self.writer.calls[0][1](1, error)
        self.assertEqual(self.coordinator.state.status, RetentionStatus.FAILED)
        self.assertIs(self.coordinator.state.error, error)
        self.assertTrue(self.coordinator.retry())
        self.writer.calls[1][1](1, None)
        self.assertEqual(self.coordinator.state.status, RetentionStatus.DURABLE)

    def test_stale_completion_cannot_publish_newer_state(self):
        self.coordinator.edit(1)
        self.coordinator.flush()
        self.current["text"] = "two"
        self.coordinator.edit(2)
        self.assertFalse(self.coordinator.complete(999, 1))
        self.assertEqual(self.coordinator.state.durable_revision, None)

    def test_timer_firing_during_write_does_not_lose_later_edit(self):
        self.coordinator.edit(1)
        self.clock.now = 1.0
        self.scheduler.run_due()
        self.current["text"] = "two"
        self.coordinator.edit(2)
        self.clock.now = 2.0
        self.scheduler.run_due()
        self.writer.calls[0][1](1, None)
        self.scheduler.run_due()
        self.assertEqual(len(self.writer.calls), 2)

    def test_failed_attempt_completion_cannot_complete_retry_attempt(self):
        self.coordinator.edit(1)
        self.assertFalse(self.coordinator.flush())
        first_complete = self.writer.calls[0][1]
        first_complete(1, RuntimeError("disk full"))
        self.assertTrue(self.coordinator.retry())
        second_complete = self.writer.calls[1][1]
        self.assertFalse(first_complete(1, None))
        self.assertEqual(self.coordinator.state.status, RetentionStatus.WRITING)
        second_complete(1, None)
        self.assertEqual(self.coordinator.state.status, RetentionStatus.DURABLE)

if __name__ == "__main__":
    unittest.main()
