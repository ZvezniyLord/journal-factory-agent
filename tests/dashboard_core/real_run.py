from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Dashboard Core real-run harness")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="keep the verified backend running for manual browser inspection",
    )
    arguments = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="journal-factory-dashboard-") as temp:
        root = Path(temp)
        source, output = _create_sample_tree(root)
        state_store = JsonDashboardStateStore(output / "dashboard-state")
        workspace = DeterministicWorkspaceAdapter()
        discovery = RecursiveDiscoveryAdapter()
        excel_locator = SuffixCandidateLocator(
            kind="excel",
            suffixes={".xlsx", ".xls"},
        )
        article_locator = SuffixCandidateLocator(
            kind="article",
            suffixes={".docx", ".doc"},
        )
        orchestrator = DeterministicOrchestratorAdapter()
        clock = FixedClock()

        service = _make_service(
            workspace=workspace,
            discovery=discovery,
            excel_locator=excel_locator,
            article_locator=article_locator,
            orchestrator=orchestrator,
            state_store=state_store,
            clock=clock,
        )
        server = DashboardHttpServer(service, port=0)
        server.start()
        try:
            start_status, start_response = _json_request(
                server.base_url,
                "POST",
                "/api/dashboard/runs",
                {
                    "source_folder": str(source),
                    "output_folder": str(output),
                    "journal_number": "137",
                },
            )
            _require(start_status == 201, "start endpoint did not return 201")
            started = start_response["run"]
            run_id = str(started["run_id"])
            _verify_success_snapshot(started)
            _require(discovery.calls[0][1], "discovery was not recursive")
            persisted_path = state_store.state_path(run_id)
            persisted_json = json.loads(persisted_path.read_text(encoding="utf-8"))
            _require(persisted_json["run_id"] == run_id, "persisted run ID differs")
        finally:
            server.stop()

        interrupted = state_store.load(run_id).evolve(
            state=RunState.RUNNING,
            stage="interrupted_for_real_run",
            final_result=None,
            updated_at=clock(),
        )
        state_store.save(interrupted)
        restarted_service = _make_service(
            workspace=workspace,
            discovery=discovery,
            excel_locator=excel_locator,
            article_locator=article_locator,
            orchestrator=orchestrator,
            state_store=state_store,
            clock=clock,
        )
        restarted_server = DashboardHttpServer(restarted_service, port=0)
        restarted_server.start()
        try:
            recovery_status, recovery_response = _json_request(
                restarted_server.base_url,
                "GET",
                f"/api/dashboard/runs/{run_id}",
            )
            _require(recovery_status == 200, "recovery endpoint did not return 200")
            _require(
                recovery_response["run"]["stage"] == "interrupted_for_real_run",
                "fresh backend did not load the persisted interrupted state",
            )
            resume_status, resume_response = _json_request(
                restarted_server.base_url,
                "POST",
                f"/api/dashboard/runs/{run_id}/resume",
                {},
            )
            _require(resume_status == 200, "resume endpoint did not return 200")
            _verify_success_snapshot(resume_response["run"])

            discovery.failure = DashboardPortError(
                code="REAL_RUN_DISCOVERY_FAILURE",
                message="Deterministic real-run failure detail",
                retryable=True,
            )
            failure_status, failure_response = _json_request(
                restarted_server.base_url,
                "POST",
                "/api/dashboard/runs",
                {
                    "source_folder": str(source),
                    "output_folder": str(output),
                    "journal_number": "138",
                },
            )
            _require(failure_status == 502, "failure endpoint did not return 502")
            _require(
                failure_response["error"]["code"] == "SOURCE_DISCOVERY_FAILED",
                "discovery failure code was not preserved",
            )
            _require(
                "Deterministic real-run failure detail"
                not in json.dumps(failure_response),
                "adapter failure detail leaked to the HTTP response",
            )

            evidence = {
                "backend_url": restarted_server.base_url,
                "temporary_source": str(source),
                "temporary_output": str(output),
                "run_id": run_id,
                "recursive_discovery": discovery.calls[0][1],
                "discovered_files": [
                    item.file_id
                    for item in orchestrator.submissions[0].discovery.files
                ],
                "excel_candidate_count": started["excel_candidate_count"],
                "article_candidate_count": started["article_candidate_count"],
                "core_states": {
                    item["core_id"]: item["state"] for item in started["cores"]
                },
                "warning_codes": [
                    item["code"] for item in started["warnings"]
                ],
                "report_ids": [
                    item["record_id"] for item in started["reports"]
                ],
                "file_ids": [item["record_id"] for item in started["files"]],
                "final_result": started["final_result"],
                "persisted_state": str(persisted_path),
                "persisted_json_valid": persisted_json["schema_version"] == 1,
                "restart_recovered_stage": recovery_response["run"]["stage"],
                "resume_state": resume_response["run"]["state"],
                "structured_failure": failure_response["error"],
                "traceback_exposed": "Traceback" in json.dumps(failure_response),
                "manual_urls": {
                    "health": f"{restarted_server.base_url}/health",
                    "successful_run": (
                        f"{restarted_server.base_url}/api/dashboard/runs/{run_id}"
                    ),
                    "failed_run": (
                        f"{restarted_server.base_url}/api/dashboard/runs/run-138"
                    ),
                },
            }
            print(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True))
            if arguments.serve:
                print("Dashboard real-run server is active. Press Ctrl+C to stop.")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
        finally:
            restarted_server.stop()
    return 0


def _make_service(
    *,
    workspace: DeterministicWorkspaceAdapter,
    discovery: RecursiveDiscoveryAdapter,
    excel_locator: SuffixCandidateLocator,
    article_locator: SuffixCandidateLocator,
    orchestrator: DeterministicOrchestratorAdapter,
    state_store: JsonDashboardStateStore,
    clock: FixedClock,
) -> DashboardService:
    return DashboardService(
        workspace_driver=workspace,
        source_discovery=discovery,
        excel_candidate_locator=excel_locator,
        article_candidate_locator=article_locator,
        orchestrator=orchestrator,
        state_store=state_store,
        clock=clock,
    )


def _create_sample_tree(root: Path) -> tuple[Path, Path]:
    source = root / "source"
    output = root / "output"
    (source / "conference" / "articles" / "nested").mkdir(parents=True)
    (source / "conference" / "assets").mkdir(parents=True)
    output.mkdir()
    (source / "conference" / "registry.xlsx").write_bytes(b"registry")
    (source / "conference" / "articles" / "alpha.docx").write_bytes(b"alpha")
    (
        source / "conference" / "articles" / "nested" / "beta.doc"
    ).write_bytes(b"beta")
    (source / "conference" / "assets" / "cover.png").write_bytes(b"cover")
    return source, output


def _verify_success_snapshot(snapshot: dict[str, Any]) -> None:
    _require(
        snapshot["state"] == "succeeded_with_warnings",
        "run did not finish with the expected warning state",
    )
    _require(snapshot["discovered_file_count"] == 4, "recursive file count differs")
    _require(snapshot["excel_candidate_count"] == 1, "Excel count differs")
    _require(snapshot["article_candidate_count"] == 2, "article count differs")
    _require(len(snapshot["reports"]) == 1, "report collection differs")
    _require(len(snapshot["files"]) == 1, "file collection differs")
    _require(snapshot["progress_percent"] == 100.0, "progress is not complete")


def _json_request(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url}{path}",
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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


if __name__ == "__main__":
    raise SystemExit(main())
