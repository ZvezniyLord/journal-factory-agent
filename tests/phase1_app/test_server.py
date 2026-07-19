from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from journal_factory.phase1_app.composition import build_application
from journal_factory.phase1_app.server import Phase1HttpServer


class FakeDialog:
    def __init__(self, source: Path, output: Path) -> None:
        self.source = source
        self.output = output
        self.calls: list[str] = []

    def select(self, kind: str) -> str | None:
        self.calls.append(kind)
        if kind in {"source_file", "source_folder"}:
            return str(self.source)
        if kind == "output_folder":
            return str(self.output)
        raise AssertionError(kind)


class Phase1ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "conference.zip"
        self.source.write_bytes(b"conference")
        self.output = self.root / "output"
        self.output.mkdir()
        self.desktop = self.root / "Desktop"
        self.desktop.mkdir()
        self.dialog = FakeDialog(self.source, self.output)
        self.state_directory = self.root / "state"
        application = build_application(
            desktop_path=self.desktop,
            state_directory=self.state_directory,
            dialog=self.dialog,
        )
        index_path = Path(__file__).resolve().parents[2] / "index.html"
        self.server = Phase1HttpServer(application, index_path=index_path)
        self.server.start()

    def tearDown(self) -> None:
        self.server.stop()
        self.temporary.cleanup()

    def request(self, path: str, method: str = "GET", body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            self.server.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                payload = response.read()
                content_type = response.headers["Content-Type"]
                return response.status, content_type, payload
        except urllib.error.HTTPError as error:
            try:
                return error.code, error.headers["Content-Type"], error.read()
            finally:
                error.close()

    def json_request(self, path: str, method: str = "GET", body=None):
        status, _, payload = self.request(path, method, body)
        return status, json.loads(payload)

    def valid_request(self):
        return {
            "source_path": str(self.source),
            "output_parent": str(self.output),
            "journal_number": "95",
        }

    def test_root_is_real_phase1_interface_with_every_required_control(self) -> None:
        status, content_type, payload = self.request("/")
        html = payload.decode("utf-8")

        self.assertEqual(200, status)
        self.assertIn("text/html", content_type)
        for element_id in (
            "source-path",
            "select-source",
            "output-parent",
            "select-output",
            "journal-number",
            "workspace-path",
            "validate-workspace",
            "create-workspace",
            "start-run",
            "refresh-run",
            "resume-run",
            "report-paths",
            "output-paths",
        ):
            self.assertIn(f'id="{element_id}"', html)
        for route in (
            "/api/workspace/defaults",
            "/api/workspace/validate",
            "/api/workspace/create",
            "/api/runs/start",
            "/api/select",
        ):
            self.assertIn(route, html)
        self.assertNotIn("path.join", html)
        self.assertNotIn("\\\\Desktop\\\\", html)

    def test_defaults_validate_and_invalid_feedback_are_server_computed(self) -> None:
        status, defaults = self.json_request("/api/workspace/defaults")
        invalid_status, invalid = self.json_request(
            "/api/workspace/validate", "POST", {**self.valid_request(), "journal_number": ""}
        )
        valid_status, valid = self.json_request(
            "/api/workspace/validate", "POST", self.valid_request()
        )

        self.assertEqual(200, status)
        self.assertEqual(str(self.desktop.resolve()), defaults["output_parent"])
        self.assertEqual(422, invalid_status)
        self.assertEqual("JOURNAL_NUMBER_REQUIRED", invalid["error"]["code"])
        self.assertNotIn("Traceback", json.dumps(invalid))
        self.assertEqual(200, valid_status)
        self.assertEqual(str((self.output / "95").resolve()), valid["workspace"]["workspace_path"])

    def test_selection_controls_call_real_dialog_bridge(self) -> None:
        file_status, selected_file = self.json_request(
            "/api/select", "POST", {"kind": "source_file"}
        )
        output_status, selected_output = self.json_request(
            "/api/select", "POST", {"kind": "output_folder"}
        )

        self.assertEqual(200, file_status)
        self.assertEqual(str(self.source), selected_file["path"])
        self.assertEqual(200, output_status)
        self.assertEqual(str(self.output), selected_output["path"])
        self.assertEqual(["source_file", "output_folder"], self.dialog.calls)

    def test_create_start_refresh_resume_expose_real_artifact_paths(self) -> None:
        create_status, created = self.json_request(
            "/api/workspace/create", "POST", self.valid_request()
        )
        run_id = created["workspace"]["run_id"]
        start_status, started = self.json_request(
            "/api/runs/start", "POST", {**self.valid_request(), "run_id": run_id}
        )
        refresh_status, refreshed = self.json_request(f"/api/runs/{run_id}")
        resume_status, resumed = self.json_request(
            f"/api/runs/{run_id}/resume", "POST", {}
        )

        self.assertEqual(201, create_status)
        self.assertEqual(200, start_status)
        self.assertIn(started["run"]["state"], {"succeeded", "succeeded_with_warnings"})
        self.assertEqual(100.0, started["run"]["progress_percent"])
        self.assertNotIn("running", {core["state"] for core in started["run"]["cores"]})
        self.assertEqual(200, refresh_status)
        self.assertEqual(run_id, refreshed["workspace"]["run_id"])
        self.assertEqual(200, resume_status)
        self.assertEqual(run_id, resumed["run"]["run_id"])

        reports = started["workspace"]["reports"]
        paths = started["workspace"]["paths"]
        self.assertTrue(all(Path(path).is_absolute() for path in reports.values()))
        self.assertTrue(all(Path(path).is_absolute() for path in paths.values()))
        self.assertTrue(all(Path(path).exists() for path in reports.values()))
        self.assertEqual(reports, refreshed["workspace"]["reports"])
        dashboard = json.loads(Path(reports["dashboard_state"]).read_text(encoding="utf-8"))
        self.assertEqual(run_id, dashboard["run_id"])

    def test_malformed_json_is_structured_and_contains_no_traceback(self) -> None:
        request = urllib.request.Request(
            self.server.base_url + "/api/workspace/validate",
            data=b"{bad",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=5)
        try:
            payload = caught.exception.read().decode("utf-8")
        finally:
            caught.exception.close()

        self.assertEqual(400, caught.exception.code)
        self.assertIn("HTTP_JSON_INVALID", payload)
        self.assertNotIn("Traceback", payload)

    def test_run_view_is_reconstructed_after_backend_restart(self) -> None:
        _, created = self.json_request(
            "/api/workspace/create", "POST", self.valid_request()
        )
        run_id = created["workspace"]["run_id"]
        start_status, started = self.json_request(
            "/api/runs/start", "POST", {**self.valid_request(), "run_id": run_id}
        )
        self.assertEqual(200, start_status)
        self.server.stop()

        restarted_application = build_application(
            desktop_path=self.desktop,
            state_directory=self.state_directory,
            dialog=self.dialog,
        )
        index_path = Path(__file__).resolve().parents[2] / "index.html"
        self.server = Phase1HttpServer(restarted_application, index_path=index_path)
        self.server.start()
        status, restored = self.json_request(f"/api/runs/{run_id}")

        self.assertEqual(200, status)
        self.assertEqual(started["run"]["revision"], restored["run"]["revision"])
        self.assertEqual(started["run"]["state"], restored["run"]["state"])
        self.assertEqual(started["workspace"]["reports"], restored["workspace"]["reports"])


if __name__ == "__main__":
    unittest.main()
