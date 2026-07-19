from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from journal_factory.dashboard_core.backend import DashboardHttpServer
from journal_factory.dashboard_core.models import RunState
from journal_factory.dashboard_core.persistence import JsonDashboardStateStore
from journal_factory.dashboard_core.ports import DashboardPortError
from journal_factory.dashboard_core.service import DashboardService
from tests.dashboard_core.adapters import (
    DeterministicOrchestratorAdapter,
    DeterministicWorkspaceAdapter,
    FixedClock,
    RecursiveDiscoveryAdapter,
    SuffixCandidateLocator,
)


class DashboardHttpServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.source = root / "source"
        self.output = root / "output"
        self.state_directory = root / "dashboard-state"
        (self.source / "nested" / "articles").mkdir(parents=True)
        self.output.mkdir()
        (self.source / "nested" / "registry.xlsx").write_bytes(b"registry")
        (self.source / "nested" / "articles" / "alpha.docx").write_bytes(
            b"alpha"
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
        self.store = JsonDashboardStateStore(self.state_directory)
        self.clock = FixedClock()
        self.server = self._start_server(self._make_service())

    def tearDown(self) -> None:
        self.server.stop()
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

    def _start_server(self, service: DashboardService) -> DashboardHttpServer:
        server = DashboardHttpServer(service, port=0)
        server.start()
        return server

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | bytes | None = None,
    ) -> tuple[int, dict[str, object]]:
        data: bytes | None
        if isinstance(payload, dict):
            data = json.dumps(payload).encode("utf-8")
        else:
            data = payload
        request = Request(
            f"{self.server.base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read().decode("utf-8"))
            finally:
                error.close()

    def _start_payload(self) -> dict[str, object]:
        return {
            "source_folder": str(self.source),
            "output_folder": str(self.output),
            "journal_number": "137",
        }

    def test_health_start_and_get_routes_expose_dashboard_state(self) -> None:
        health_status, health = self._request("GET", "/health")
        start_status, started = self._request(
            "POST",
            "/api/dashboard/runs",
            self._start_payload(),
        )
        run_id = started["run"]["run_id"]
        get_status, recovered = self._request(
            "GET",
            f"/api/dashboard/runs/{run_id}",
        )

        self.assertEqual(health_status, 200)
        self.assertEqual(health, {"status": "ok"})
        self.assertEqual(start_status, 201)
        self.assertEqual(started["run"]["state"], "succeeded_with_warnings")
        self.assertEqual(started["run"]["discovered_file_count"], 2)
        self.assertEqual(started["run"]["excel_candidate_count"], 1)
        self.assertEqual(started["run"]["article_candidate_count"], 1)
        self.assertEqual(get_status, 200)
        self.assertEqual(recovered, started)
        self.assertTrue(self.discovery.calls[0][1])

    def test_fresh_backend_process_reads_persisted_run(self) -> None:
        _, started = self._request(
            "POST",
            "/api/dashboard/runs",
            self._start_payload(),
        )
        run_id = started["run"]["run_id"]
        self.server.stop()
        self.server = self._start_server(self._make_service())

        status, recovered = self._request(
            "GET",
            f"/api/dashboard/runs/{run_id}",
        )

        self.assertEqual(status, 200)
        self.assertEqual(recovered, started)

    def test_resume_route_uses_orchestrator_resume_for_interrupted_state(self) -> None:
        _, started = self._request(
            "POST",
            "/api/dashboard/runs",
            self._start_payload(),
        )
        run_id = started["run"]["run_id"]
        persisted = self.store.load(run_id)
        interrupted = persisted.evolve(
            state=RunState.RUNNING,
            stage="interrupted",
            final_result=None,
            updated_at=self.clock(),
        )
        self.store.save(interrupted)
        self.server.stop()
        self.server = self._start_server(self._make_service())

        status, response = self._request(
            "POST",
            f"/api/dashboard/runs/{run_id}/resume",
            {},
        )

        self.assertEqual(status, 200)
        self.assertEqual(response["run"]["state"], "succeeded_with_warnings")
        self.assertEqual(self.workspace.restore_requests, [run_id])
        self.assertEqual(self.orchestrator.resume_requests, [run_id])

    def test_invalid_json_and_unsupported_method_are_structured(self) -> None:
        invalid_status, invalid = self._request(
            "POST",
            "/api/dashboard/runs",
            b"{broken",
        )
        method_status, method = self._request("PUT", "/api/dashboard/runs", {})

        self.assertEqual(invalid_status, 400)
        self.assertEqual(invalid["error"]["code"], "INVALID_DASHBOARD_REQUEST")
        self.assertNotIn("Traceback", json.dumps(invalid))
        self.assertEqual(method_status, 405)
        self.assertEqual(method["error"]["code"], "METHOD_NOT_ALLOWED")

    def test_typed_discovery_failure_returns_browser_safe_response(self) -> None:
        self.discovery.failure = DashboardPortError(
            code="TEST_DISCOVERY_FAILED",
            message="Sensitive adapter detail",
            retryable=True,
        )

        status, response = self._request(
            "POST",
            "/api/dashboard/runs",
            self._start_payload(),
        )

        self.assertEqual(status, 502)
        self.assertEqual(response["error"]["code"], "SOURCE_DISCOVERY_FAILED")
        self.assertTrue(response["error"]["retryable"])
        self.assertEqual(response["run"]["state"], "failed")
        self.assertNotIn("Sensitive adapter detail", json.dumps(response))
        self.assertNotIn("Traceback", json.dumps(response))

    def test_server_rejects_non_loopback_binding(self) -> None:
        with self.assertRaisesRegex(ValueError, "loopback"):
            DashboardHttpServer(self._make_service(), host="0.0.0.0", port=0)


if __name__ == "__main__":
    unittest.main()
