from __future__ import annotations

import unittest

from spikes.peer_frames.application_lifecycle import (
    ApplicationExitDisposition,
    ApplicationExitPhase,
    ApplicationExitResult,
    ApplicationFrameLifecycle,
    ApplicationShutdownCoordinator,
    CleanupStep,
    DefaultTemplateUnreadable,
    ZeroFrameResult,
    WorkspaceShutdownResult,
)


class ApplicationShutdownCoordinatorTests(unittest.TestCase):
    def coordinator(self):
        calls = []
        logs = []
        exits = []
        replacements = []
        coordinator = ApplicationShutdownCoordinator(
            confirm_exit=lambda disposition: calls.append(
                ("confirm", disposition)
            ) or True,
            request_workspace_shutdown=lambda: calls.append(("workspace",)) or True,
            cleanup_steps=tuple(
                CleanupStep(name, lambda name=name: calls.append((name,)))
                for name in ("config", "history", "server", "kernels", "tools", "threads", "projectors", "backend")
            ),
            finish_quit=exits.append,
            replace_process=lambda: replacements.append(True),
            log_error=logs.append,
        )
        return coordinator, calls, logs, exits, replacements

    def test_quit_commits_workspace_then_cleans_once_in_order(self):
        coordinator, calls, logs, exits, replacements = self.coordinator()

        result = coordinator.request(ApplicationExitDisposition.QUIT)

        self.assertEqual(result, ApplicationExitResult.COMPLETED)
        self.assertEqual(
            calls,
            [("confirm", ApplicationExitDisposition.QUIT), ("workspace",),
             ("config",), ("history",), ("server",), ("kernels",),
             ("tools",), ("threads",), ("projectors",), ("backend",)],
        )
        self.assertEqual(exits, [0])
        self.assertEqual(replacements + logs, [])
        self.assertEqual(coordinator.phase, ApplicationExitPhase.FINISHED)

    def test_confirmation_or_workspace_veto_restores_idle_without_cleanup(self):
        coordinator, calls, _logs, exits, replacements = self.coordinator()
        coordinator._confirm_exit = lambda _disposition: False

        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.QUIT),
            ApplicationExitResult.CANCELLED,
        )
        self.assertEqual(calls, [])
        self.assertEqual(exits + replacements, [])
        self.assertEqual(coordinator.phase, ApplicationExitPhase.IDLE)

    def test_persistence_failure_cancels_before_workspace_or_shell_cleanup(self):
        coordinator, calls, logs, exits, replacements = self.coordinator()

        def fail_persistence():
            calls.append(("persistence",))
            raise OSError("read-only workspace store")

        coordinator._prepare_cleanup = fail_persistence

        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.QUIT),
            ApplicationExitResult.CANCELLED,
        )
        self.assertEqual(
            calls,
            [("confirm", ApplicationExitDisposition.QUIT), ("persistence",)],
        )
        self.assertIn("application persistence preflight failed", logs[0])
        self.assertEqual(exits + replacements, [])
        self.assertEqual(coordinator.phase, ApplicationExitPhase.IDLE)
        self.assertIsNone(coordinator.disposition)

        coordinator._confirm_exit = lambda _disposition: True
        coordinator._request_workspace_shutdown = lambda: False
        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.RESTART),
            ApplicationExitResult.CANCELLED,
        )
        self.assertEqual(exits + replacements, [])
        self.assertEqual(coordinator.phase, ApplicationExitPhase.IDLE)

    def test_reentrant_and_conflicting_requests_coalesce_first_disposition(self):
        coordinator, _calls, _logs, exits, replacements = self.coordinator()
        nested = []

        def confirm(disposition):
            nested.append(coordinator.request(ApplicationExitDisposition.RESTART))
            self.assertEqual(coordinator.disposition, disposition)
            return True

        coordinator._confirm_exit = confirm

        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.QUIT),
            ApplicationExitResult.COMPLETED,
        )
        self.assertEqual(nested, [ApplicationExitResult.COALESCED])
        self.assertEqual(coordinator.disposition, ApplicationExitDisposition.QUIT)
        self.assertEqual(exits, [0])
        self.assertEqual(replacements, [])

    def test_request_during_cleanup_is_coalesced(self):
        coordinator, _calls, _logs, exits, _replacements = self.coordinator()
        nested = []
        coordinator._cleanup_steps = (
            CleanupStep(
                "nested",
                lambda: nested.append(
                    coordinator.request(ApplicationExitDisposition.RESTART)
                ),
            ),
        )

        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.QUIT),
            ApplicationExitResult.COMPLETED,
        )
        self.assertEqual(nested, [ApplicationExitResult.COALESCED])
        self.assertEqual(exits, [0])

    def test_all_cleanup_runs_and_quit_exits_one_after_failures(self):
        coordinator, calls, logs, exits, _replacements = self.coordinator()

        def fail_config():
            calls.append(("config",))
            raise OSError("read-only")

        def fail_kernel():
            calls.append(("kernels",))
            raise RuntimeError("broker stuck")

        coordinator._cleanup_steps = (
            CleanupStep("config", fail_config),
            CleanupStep("history", lambda: calls.append(("history",))),
            CleanupStep("kernels", fail_kernel),
            CleanupStep("backend", lambda: calls.append(("backend",))),
        )

        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.QUIT),
            ApplicationExitResult.COMPLETED,
        )
        self.assertEqual(calls[-4:], [("config",), ("history",), ("kernels",), ("backend",)])
        self.assertEqual(len(logs), 2)
        self.assertEqual(exits, [1])

    def test_committed_workspace_cleanup_errors_join_later_cleanup_errors(self):
        coordinator, calls, logs, exits, _replacements = self.coordinator()
        coordinator._request_workspace_shutdown = lambda: WorkspaceShutdownResult(
            True, ("committed pane cleanup failed (shell): broker stuck",)
        )

        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.QUIT),
            ApplicationExitResult.COMPLETED,
        )
        self.assertEqual(len(logs), 1)
        self.assertIn("shell", logs[0])
        self.assertEqual(calls[-1], ("backend",))
        self.assertEqual(exits, [1])

    def test_restart_continues_after_cleanup_failure(self):
        coordinator, _calls, logs, exits, replacements = self.coordinator()
        coordinator._cleanup_steps = (
            CleanupStep("config", lambda: (_ for _ in ()).throw(OSError("bad"))),
        )

        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.RESTART),
            ApplicationExitResult.COMPLETED,
        )
        self.assertEqual(replacements, [True])
        self.assertEqual(exits, [])
        self.assertEqual(len(logs), 1)

    def test_restart_replacement_failure_logs_and_exits_one(self):
        coordinator, _calls, logs, exits, _replacements = self.coordinator()
        coordinator._replace_process = lambda: (_ for _ in ()).throw(
            OSError("exec denied")
        )

        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.RESTART),
            ApplicationExitResult.FAILED,
        )
        self.assertIn("exec denied", logs[-1])
        self.assertEqual(exits, [1])

    def test_negotiation_exception_is_precommit_failure(self):
        coordinator, calls, logs, exits, replacements = self.coordinator()
        coordinator._request_workspace_shutdown = lambda: (_ for _ in ()).throw(
            RuntimeError("policy failed")
        )

        self.assertEqual(
            coordinator.request(ApplicationExitDisposition.QUIT),
            ApplicationExitResult.FAILED,
        )
        self.assertEqual(calls, [("confirm", ApplicationExitDisposition.QUIT)])
        self.assertIn("policy failed", logs[-1])
        self.assertEqual(exits + replacements, [])
        self.assertEqual(coordinator.phase, ApplicationExitPhase.IDLE)


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

    def test_startup_initialization_composes_existing_temporary_frames(self):
        lifecycle, frames, _quits, configured, factory, logs, fatals = (
            self.controller()
        )
        frames.extend(("editor-frame", "shell-frame", "tool-frame"))

        def compose():
            configured.append(True)
            frames[:] = ["default-frame"]

        lifecycle._create_configured_frame = compose

        self.assertEqual(
            lifecycle.initialize_default_frame(), ZeroFrameResult.FRAME_CREATED
        )
        self.assertEqual(frames, ["default-frame"])
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
