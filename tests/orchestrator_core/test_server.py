import json
import threading
import unittest
import urllib.error
import urllib.request

from journal_factory.orchestrator_core.server import OrchestratorApplication, make_server


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.application = OrchestratorApplication()
        self.server = make_server("127.0.0.1", 0, self.application)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def get(self, path: str):
        with urllib.request.urlopen(self.base_url + path, timeout=2) as response:
            return response.status, response.headers, response.read()

    def post(self, path: str, body: bytes):
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, response.headers, response.read()

    def test_serves_thin_root_menu_and_completes_demo_run(self) -> None:
        status, _, html = self.get("/")
        _, _, initial_body = self.get("/api/orchestrator/state")
        _, _, started_body = self.post(
            "/api/orchestrator/start", json.dumps({"run_id": "smoke-run"}).encode()
        )

        initial = json.loads(initial_body)
        started = json.loads(started_body)
        self.assertEqual(200, status)
        self.assertIn(b'id="start-run"', html)
        self.assertIn(b'id="run-state"', html)
        self.assertEqual("idle", initial["state"])
        self.assertEqual("completed", started["state"])
        self.assertEqual(["bootstrap"], started["completed_cores"])
        self.assertGreater(started["action_count"], 0)

    def test_malformed_json_returns_structured_error_without_traceback(self) -> None:
        request = urllib.request.Request(
            self.base_url + "/api/orchestrator/start",
            data=b"{bad json",
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=2)

        try:
            body = caught.exception.read().decode("utf-8")
        finally:
            caught.exception.close()
        payload = json.loads(body)
        self.assertEqual(400, caught.exception.code)
        self.assertEqual("HTTP_JSON_INVALID", payload["error"]["code"])
        self.assertNotIn("Traceback", body)


if __name__ == "__main__":
    unittest.main()
