from __future__ import annotations

import unittest

from spikes.peer_frames.application_lifecycle import (
    ApplicationFrameLifecycle,
    DefaultTemplateUnreadable,
    ZeroFrameResult,
)


class ApplicationFrameLifecycleTests(unittest.TestCase):
    def controller(self, *, independent=True):
        frames = []
        quits = []
        configured = []
        factory = []
        logs = []
        fatals = []

        lifecycle = ApplicationFrameLifecycle(
            has_independent_handle=lambda: independent,
            frame_count=lambda: len(frames),
            request_quit=lambda: quits.append(True),
            create_configured_frame=lambda: configured.append(True),
            create_factory_frame=lambda: factory.append(True),
            log_error=logs.append,
            fatal_exit=lambda code, message: fatals.append((code, message)),
        )
        return lifecycle, frames, quits, configured, factory, logs, fatals

    def test_zero_frames_survive_only_with_independent_application_handle(self):
        capable = self.controller(independent=True)
        conventional = self.controller(independent=False)

        self.assertEqual(
            capable[0].zero_frames_reached(), ZeroFrameResult.SURVIVING
        )
        self.assertEqual(capable[2], [])
        self.assertEqual(
            conventional[0].zero_frames_reached(),
            ZeroFrameResult.QUIT_REQUESTED,
        )
        self.assertEqual(conventional[2], [True])

    def test_existing_frame_makes_activation_and_zero_callback_noops(self):
        lifecycle, frames, quits, configured, factory, _logs, _fatals = (
            self.controller()
        )
        frames.append("frame")

        self.assertEqual(
            lifecycle.zero_frames_reached(), ZeroFrameResult.FRAME_EXISTS
        )
        self.assertEqual(
            lifecycle.application_activated(), ZeroFrameResult.FRAME_EXISTS
        )
        self.assertEqual(quits + configured + factory, [])

    def test_activation_constructs_configured_default_frame_once(self):
        lifecycle, frames, _quits, configured, factory, logs, fatals = (
            self.controller()
        )

        def create():
            configured.append(True)
            frames.append("frame")

        lifecycle._create_configured_frame = create

        self.assertEqual(
            lifecycle.application_activated(), ZeroFrameResult.FRAME_CREATED
        )
        self.assertEqual(configured, [True])
        self.assertEqual(factory + logs + fatals, [])

    def test_unreadable_configured_template_logs_and_uses_factory(self):
        lifecycle, frames, _quits, configured, factory, logs, fatals = (
            self.controller()
        )

        def configured_failure():
            configured.append(True)
            raise DefaultTemplateUnreadable("bad topology")

        def create_factory():
            factory.append(True)
            frames.append("factory-frame")

        lifecycle._create_configured_frame = configured_failure
        lifecycle._create_factory_frame = create_factory

        self.assertEqual(
            lifecycle.application_activated(), ZeroFrameResult.FRAME_CREATED
        )
        self.assertEqual(configured, [True])
        self.assertEqual(factory, [True])
        self.assertIn("bad topology", logs[0])
        self.assertEqual(fatals, [])

    def test_no_constructed_pane_is_fatal_with_exit_status_one(self):
        lifecycle, _frames, _quits, configured, factory, logs, fatals = (
            self.controller()
        )

        self.assertEqual(
            lifecycle.application_activated(), ZeroFrameResult.FATAL
        )
        self.assertEqual(configured, [True])
        self.assertEqual(factory, [True])
        self.assertIn("could not construct any pane", logs[-1])
        self.assertEqual(fatals[-1][0], 1)

    def test_factory_exception_is_fatal_with_detail(self):
        lifecycle, _frames, _quits, _configured, factory, logs, fatals = (
            self.controller()
        )

        def configured_failure():
            raise DefaultTemplateUnreadable("missing")

        def factory_failure():
            factory.append(True)
            raise RuntimeError("widgets unavailable")

        lifecycle._create_configured_frame = configured_failure
        lifecycle._create_factory_frame = factory_failure

        self.assertEqual(
            lifecycle.application_activated(), ZeroFrameResult.FATAL
        )
        self.assertEqual(factory, [True])
        self.assertIn("widgets unavailable", logs[-1])
        self.assertEqual(fatals[-1][0], 1)

    def test_reentrant_activation_is_coalesced_without_queue_growth(self):
        lifecycle, frames, _quits, configured, _factory, _logs, _fatals = (
            self.controller()
        )
        nested_results = []

        def create():
            configured.append(True)
            nested_results.extend(
                lifecycle.application_activated() for _ in range(10)
            )
            self.assertTrue(lifecycle.has_pending_activation)
            frames.append("frame")

        lifecycle._create_configured_frame = create

        self.assertEqual(
            lifecycle.application_activated(), ZeroFrameResult.FRAME_CREATED
        )
        self.assertEqual(
            nested_results, [ZeroFrameResult.COALESCED] * 10
        )
        self.assertFalse(lifecycle.creating_default_frame)
        self.assertFalse(lifecycle.has_pending_activation)
        self.assertEqual(configured, [True])


if __name__ == "__main__":
    unittest.main()
