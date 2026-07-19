from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from journal_factory.dashboard_core.models import RunState, StartRunRequest
from journal_factory.dashboard_core.ports import DashboardOperationError, DashboardPortError
from journal_factory.dashboard_core.service import DashboardService
from tests.dashboard_core.adapters import (
    DeterministicOrchestratorAdapter,
    DeterministicWorkspaceAdapter,
    FixedClock,
    MemoryStateStore,
    RecursiveDiscoveryAdapter,
    SuffixCandidateLocator,
)


class DashboardServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.source = root / "source"
        self.output = root / "output"
        (self.source / "conference" / "articles" / "nested").mkdir(parents=True)
        (self.source / "conference" / "assets").mkdir(parents=True)
        self.output.mkdir()
        (self.source / "conference" / "registry.xlsx").write_bytes(b"registry")
        (self.source / "conference" / "articles" / "alpha.docx").write_bytes(
            b"alpha"
        )
        (
            self.source
            / "conference"
            / "articles"
            / "nested"
            / "beta.doc"
        ).write_bytes(b"beta")
        (self.source / "conference" / "assets" / "cover.png").write_bytes(
            b"cover"
        )

        self.workspace = DeterministicWorkspaceAdapter()
        self.discovery = RecursiveDiscoveryAdapter()
        self.excel_locator = SuffixCandidateLocator(
            kind="excel",
            suffixes={".xlsx", ".xls"},
        )
        self.article_locator = SuffixCandidateLocator(
            kind="article",
            suffixes={".docx", ".doc"},
        )
        self.orchestrator = DeterministicOrchestratorAdapter()
        self.store = MemoryStateStore()
        self.clock = FixedClock()
        self.service = self._make_service()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _make_service(self) -> DashboardService:
        return DashboardService(
            workspace_driver=self.workspace,
            source_discovery=self.discovery,
            excel_candidate_locator=self.excel_locator,
            article_candidate_locator=self.article_locator,
            orchestrator=self.orchestrator,
            state_store=self.store,
            clock=self.clock,
        )

    def _request(self) -> StartRunRequest:
        return StartRunRequest(
            source_folder=str(self.source),
            output_folder=str(self.output),
            journal_number="137",
        )

    def test_start_run_uses_all_ports_and_projects_the_complete_run(self) -> None:
        snapshot = self.service.start_run(self._request())

        self.assertEqual(self.workspace.create_requests, [self._request()])
        self.assertEqual(len(self.discovery.calls), 1)
        self.assertTrue(self.discovery.calls[0][1], "discovery must be recursive")
        self.assertIs(self.excel_locator.calls[0], self.article_locator.calls[0])
        self.assertEqual(snapshot.discovered_file_count, 4)
        self.assertEqual(snapshot.excel_candidate_count, 1)
        self.assertEqual(snapshot.article_candidate_count, 2)
        self.assertEqual(len(self.orchestrator.submissions), 1)
        submission = self.orchestrator.submissions[0]
        self.assertEqual(len(submission.excel_candidates.candidates), 1)
        self.assertEqual(len(submission.article_candidates.candidates), 2)
        self.assertEqual(snapshot.state, RunState.SUCCEEDED_WITH_WARNINGS)
        self.assertEqual(snapshot.progress_percent, 100.0)
        self.assertEqual(len(snapshot.warnings), 2)
        self.assertEqual(len(snapshot.reports), 1)
        self.assertEqual(len(snapshot.files), 1)
        self.assertEqual(snapshot.final_result.status, "PASS WITH WARNINGS")
        self.assertFalse(snapshot.final_result.production_ready)

    def test_material_states_and_events_are_persisted_incrementally(self) -> None:
        self.service.start_run(self._request())

        states = [snapshot.state for snapshot in self.store.history]
        self.assertIn(RunState.CREATING, states)
        self.assertIn(RunState.DISCOVERING, states)
        self.assertIn(RunState.LOCATING_CANDIDATES, states)
        self.assertIn(RunState.SUBMITTING, states)
        self.assertIn(RunState.RUNNING, states)
        self.assertEqual(states[-1], RunState.SUCCEEDED_WITH_WARNINGS)
        revisions = [snapshot.revision for snapshot in self.store.history]
        self.assertEqual(revisions, sorted(revisions))

    def test_blank_input_fails_before_calling_any_port(self) -> None:
        request = StartRunRequest(
            source_folder=" ",
            output_folder=str(self.output),
            journal_number="137",
        )

        with self.assertRaises(DashboardOperationError) as raised:
            self.service.start_run(request)

        self.assertEqual(raised.exception.failure.code, "INVALID_DASHBOARD_REQUEST")
        self.assertEqual(self.workspace.create_requests, [])
        self.assertIsNone(raised.exception.snapshot)

    def test_discovery_failure_is_structured_persisted_and_sanitized(self) -> None:
        self.discovery.failure = DashboardPortError(
            code="TEST_DISCOVERY_BROKEN",
            message="A private source path must not be echoed",
            retryable=True,
        )

        with self.assertRaises(DashboardOperationError) as raised:
            self.service.start_run(self._request())

        error = raised.exception
        self.assertEqual(error.failure.code, "SOURCE_DISCOVERY_FAILED")
        self.assertTrue(error.failure.retryable)
        self.assertEqual(error.failure.details["port_code"], "TEST_DISCOVERY_BROKEN")
        self.assertNotIn("private source", error.failure.message)
        self.assertNotIn("Traceback", str(error))
        self.assertEqual(error.snapshot.state, RunState.FAILED)
        self.assertEqual(self.store.snapshots[error.snapshot.run_id], error.snapshot)
        self.assertEqual(self.excel_locator.calls, [])
        self.assertEqual(self.orchestrator.submissions, [])

    def test_restart_recovery_loads_state_and_resumes_through_ports(self) -> None:
        started = self.service.start_run(self._request())
        interrupted = started.evolve(
            state=RunState.RUNNING,
            stage="orchestrator:resume",
            final_result=None,
            updated_at=self.clock(),
        )
        self.store.save(interrupted)
        restarted_service = self._make_service()

        recovered = restarted_service.get_run(started.run_id)
        resumed = restarted_service.resume_run(started.run_id)

        self.assertEqual(recovered, interrupted)
        self.assertEqual(self.workspace.restore_requests, [started.run_id])
        self.assertEqual(self.orchestrator.resume_requests, [started.run_id])
        self.assertEqual(resumed.state, RunState.SUCCEEDED_WITH_WARNINGS)
        self.assertGreater(resumed.revision, interrupted.revision)

    def test_missing_recovery_state_returns_run_not_found(self) -> None:
        with self.assertRaises(DashboardOperationError) as raised:
            self.service.get_run("missing-run")

        self.assertEqual(raised.exception.failure.code, "RUN_NOT_FOUND")
        self.assertIsNone(raised.exception.snapshot)

    def test_workspace_failure_is_structured_without_a_snapshot(self) -> None:
        self.workspace.failure = DashboardPortError(
            code="TEST_WORKSPACE_FAILED",
            message="Deterministic workspace failure",
            retryable=False,
        )

        with self.assertRaises(DashboardOperationError) as raised:
            self.service.start_run(self._request())

        self.assertEqual(
            raised.exception.failure.code,
            "WORKSPACE_OPERATION_FAILED",
        )
        self.assertIsNone(raised.exception.snapshot)
        self.assertEqual(self.discovery.calls, [])

    def test_excel_candidate_failure_has_a_dedicated_code(self) -> None:
        self.excel_locator.failure = DashboardPortError(
            code="TEST_LOCATOR_FAILED",
            message="Deterministic locator failure",
            retryable=True,
        )

        with self.assertRaises(DashboardOperationError) as raised:
            self.service.start_run(self._request())

        self.assertEqual(
            raised.exception.failure.code,
            "EXCEL_CANDIDATE_LOCATION_FAILED",
        )
        self.assertTrue(raised.exception.failure.retryable)
        self.assertEqual(raised.exception.snapshot.state, RunState.FAILED)

    def test_article_candidate_failure_has_a_dedicated_code(self) -> None:
        self.article_locator.failure = DashboardPortError(
            code="TEST_LOCATOR_FAILED",
            message="Deterministic locator failure",
            retryable=True,
        )

        with self.assertRaises(DashboardOperationError) as raised:
            self.service.start_run(self._request())

        self.assertEqual(
            raised.exception.failure.code,
            "ARTICLE_CANDIDATE_LOCATION_FAILED",
        )
        self.assertTrue(raised.exception.failure.retryable)
        self.assertEqual(raised.exception.snapshot.state, RunState.FAILED)

    def test_orchestrator_failure_is_structured_after_submission(self) -> None:
        self.orchestrator.failure = DashboardPortError(
            code="TEST_ORCHESTRATOR_FAILED",
            message="Deterministic Orchestrator failure",
            retryable=True,
        )

        with self.assertRaises(DashboardOperationError) as raised:
            self.service.start_run(self._request())

        self.assertEqual(
            raised.exception.failure.code,
            "ORCHESTRATOR_SUBMISSION_FAILED",
        )
        self.assertEqual(len(self.orchestrator.submissions), 1)
        self.assertEqual(raised.exception.snapshot.state, RunState.FAILED)

    def test_state_save_failure_is_structured(self) -> None:
        self.store.fail_save = True

        with self.assertRaises(DashboardOperationError) as raised:
            self.service.start_run(self._request())

        self.assertEqual(
            raised.exception.failure.code,
            "DASHBOARD_STATE_PERSISTENCE_FAILED",
        )
        self.assertTrue(raised.exception.failure.retryable)
        self.assertIsNotNone(raised.exception.snapshot)
        self.assertEqual(self.discovery.calls, [])


if __name__ == "__main__":
    unittest.main()
