import unittest
from datetime import datetime, timezone

from journal_factory.orchestrator_core.adapters import InMemoryActionLog
from journal_factory.orchestrator_core.contracts import (
    CoreDescriptor,
    CoreInvocationResult,
    FailureRoute,
    PauseRequest,
    ResumeRequest,
    RunRequest,
    RunState,
)
from journal_factory.orchestrator_core.errors import ErrorCode, OrchestratorError
from journal_factory.orchestrator_core.orchestrator import Orchestrator
from journal_factory.orchestrator_core.registry import CoreRegistry


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 7, 19, 20, 30, tzinfo=timezone.utc)


class ScriptedCore:
    def __init__(self, *results: CoreInvocationResult) -> None:
        self.results = list(results)
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        return self.results.pop(0)


class RaisingCore:
    def invoke(self, request):
        raise RuntimeError("private adapter detail")


class OrchestratorTests(unittest.TestCase):
    def make_orchestrator(self, registrations):
        registry = CoreRegistry()
        for descriptor, port in registrations:
            registry.register(descriptor, port)
        action_log = InMemoryActionLog()
        return Orchestrator(registry, action_log, FixedClock()), action_log

    def test_invokes_registered_cores_in_dependency_order(self) -> None:
        workspace = ScriptedCore(CoreInvocationResult.success({"ready": True}))
        article = ScriptedCore(CoreInvocationResult.success({"done": True}))
        orchestrator, _ = self.make_orchestrator(
            (
                (CoreDescriptor("workspace"), workspace),
                (CoreDescriptor("article", dependencies=("workspace",)), article),
            )
        )
        payload = {"article": {"id": "a-1"}}

        orchestrator.begin(
            RunRequest(
                run_id="run-1",
                pipeline=("workspace", "article"),
                payload_by_core={"article": payload},
            )
        )
        first = orchestrator.advance()
        final = orchestrator.advance()

        self.assertEqual(("workspace",), first.completed_cores)
        self.assertEqual(RunState.COMPLETED, final.state)
        self.assertEqual(("workspace", "article"), final.completed_cores)
        self.assertEqual("run-1:article:1", article.requests[0].request_id)
        self.assertEqual("a-1", article.requests[0].payload["article"]["id"])

    def test_retries_only_retryable_failure_within_bound(self) -> None:
        core = ScriptedCore(
            CoreInvocationResult.retryable_failure("TEMP", "try again"),
            CoreInvocationResult.success({"ok": True}),
        )
        orchestrator, actions = self.make_orchestrator(
            ((CoreDescriptor("core_a", max_retries=1), core),)
        )

        orchestrator.begin(RunRequest("run-1", ("core_a",)))
        snapshot = orchestrator.advance()

        self.assertEqual(RunState.COMPLETED, snapshot.state)
        self.assertEqual(2, snapshot.attempts["core_a"])
        self.assertEqual(2, len(core.requests))
        self.assertIn("retry_scheduled", [record.action for record in actions.records])

    def test_retry_exhaustion_fails_run(self) -> None:
        core = ScriptedCore(
            CoreInvocationResult.retryable_failure("TEMP", "one"),
            CoreInvocationResult.retryable_failure("TEMP", "two"),
        )
        orchestrator, _ = self.make_orchestrator(
            ((CoreDescriptor("core_a", max_retries=1), core),)
        )

        orchestrator.begin(RunRequest("run-1", ("core_a",)))
        snapshot = orchestrator.advance()

        self.assertEqual(RunState.FAILED, snapshot.state)
        self.assertEqual("TEMP", snapshot.failure.code)
        self.assertEqual(2, len(core.requests))

    def test_terminal_failure_is_not_retried_and_can_continue_with_warning(self) -> None:
        failed = ScriptedCore(
            CoreInvocationResult.terminal_failure("BAD_INPUT", "not retryable")
        )
        next_core = ScriptedCore(CoreInvocationResult.success())
        orchestrator, _ = self.make_orchestrator(
            (
                (
                    CoreDescriptor(
                        "optional",
                        max_retries=5,
                        failure_route=FailureRoute.CONTINUE_WITH_WARNING,
                    ),
                    failed,
                ),
                (CoreDescriptor("next_core"), next_core),
            )
        )

        orchestrator.begin(RunRequest("run-1", ("optional", "next_core")))
        warning = orchestrator.advance()
        final = orchestrator.advance()

        self.assertEqual(RunState.RUNNING, warning.state)
        self.assertEqual(1, len(failed.requests))
        self.assertEqual(RunState.COMPLETED_WITH_WARNINGS, final.state)
        self.assertEqual("BAD_INPUT", final.warnings[0].code)

    def test_pause_is_acknowledged_between_cores_and_resume_continues(self) -> None:
        first_core = ScriptedCore(CoreInvocationResult.success())
        second_core = ScriptedCore(CoreInvocationResult.success())
        orchestrator, _ = self.make_orchestrator(
            (
                (CoreDescriptor("first_core"), first_core),
                (CoreDescriptor("second_core"), second_core),
            )
        )
        orchestrator.begin(RunRequest("run-1", ("first_core", "second_core")))
        orchestrator.advance()

        requested = orchestrator.request_pause(PauseRequest("run-1", "operator"))
        paused = orchestrator.advance()
        resumed = orchestrator.resume(ResumeRequest("run-1"))
        final = orchestrator.advance()

        self.assertEqual(RunState.PAUSE_REQUESTED, requested.state)
        self.assertEqual(RunState.PAUSED, paused.state)
        self.assertEqual(RunState.RUNNING, resumed.state)
        self.assertEqual(RunState.COMPLETED, final.state)
        self.assertEqual(1, len(second_core.requests))

    def test_failure_route_can_pause_and_reject_wrong_run_resume(self) -> None:
        core = ScriptedCore(
            CoreInvocationResult.terminal_failure("REVIEW", "operator review")
        )
        orchestrator, _ = self.make_orchestrator(
            ((CoreDescriptor("core_a", failure_route=FailureRoute.PAUSE_RUN), core),)
        )
        orchestrator.begin(RunRequest("run-1", ("core_a",)))

        paused = orchestrator.advance()

        self.assertEqual(RunState.PAUSED, paused.state)
        with self.assertRaises(OrchestratorError) as caught:
            orchestrator.resume(ResumeRequest("wrong-run"))
        self.assertEqual(ErrorCode.RUN_ID_MISMATCH, caught.exception.code)

    def test_adapter_exception_becomes_typed_failure_without_private_text(self) -> None:
        orchestrator, _ = self.make_orchestrator(
            ((CoreDescriptor("core_a"), RaisingCore()),)
        )
        orchestrator.begin(RunRequest("run-1", ("core_a",)))

        snapshot = orchestrator.advance()

        self.assertEqual(RunState.FAILED, snapshot.state)
        self.assertEqual("CORE_INVOCATION_EXCEPTION", snapshot.failure.code)
        self.assertNotIn("private adapter detail", snapshot.failure.message)

    def test_action_records_are_append_only_and_sequence_ordered(self) -> None:
        core = ScriptedCore(CoreInvocationResult.success())
        orchestrator, actions = self.make_orchestrator(
            ((CoreDescriptor("core_a"), core),)
        )

        orchestrator.begin(RunRequest("run-1", ("core_a",)))
        orchestrator.advance()

        sequences = [record.sequence for record in actions.records]
        self.assertEqual(list(range(1, len(sequences) + 1)), sequences)
        self.assertEqual(len(actions.records), orchestrator.snapshot().action_count)
        self.assertTrue(all(record.timestamp_utc.endswith("Z") for record in actions.records))


if __name__ == "__main__":
    unittest.main()
