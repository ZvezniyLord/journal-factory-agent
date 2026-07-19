from __future__ import annotations

import argparse
import json
import threading
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .adapters import BootstrapCore, InMemoryActionLog, SystemClock
from .contracts import CoreDescriptor, RunRequest, RunState
from .errors import ErrorCode, OrchestratorError
from .orchestrator import Orchestrator
from .registry import CoreRegistry


TERMINAL_STATES = {
    RunState.COMPLETED,
    RunState.COMPLETED_WITH_WARNINGS,
    RunState.FAILED,
}


def create_demo_orchestrator() -> Orchestrator:
    registry = CoreRegistry()
    registry.register(CoreDescriptor("bootstrap", operation="start"), BootstrapCore())
    return Orchestrator(registry, InMemoryActionLog(), SystemClock())


class OrchestratorApplication:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._orchestrator = create_demo_orchestrator()

    def state(self) -> dict[str, Any]:
        with self._lock:
            return self._orchestrator.snapshot().to_dict()

    def start(self, run_id: str | None = None) -> dict[str, Any]:
        with self._lock:
            current = self._orchestrator.snapshot()
            if current.state in TERMINAL_STATES:
                self._orchestrator = create_demo_orchestrator()
                current = self._orchestrator.snapshot()
            if current.state is not RunState.IDLE:
                raise OrchestratorError(
                    code=ErrorCode.RUN_ALREADY_ACTIVE,
                    message="A run is already active.",
                    details={"state": current.state.value},
                )

            resolved_run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
            self._orchestrator.begin(
                RunRequest(
                    run_id=resolved_run_id,
                    pipeline=("bootstrap",),
                    payload_by_core={"bootstrap": {"command": "start"}},
                )
            )
            return self._orchestrator.run_to_terminal().to_dict()


def make_server(
    host: str,
    port: int,
    application: OrchestratorApplication | None = None,
    index_path: Path | None = None,
) -> ThreadingHTTPServer:
    if host != "127.0.0.1":
        raise ValueError("Orchestrator server must bind to 127.0.0.1")
    app = application or OrchestratorApplication()
    page_path = index_path or Path(__file__).resolve().parents[2] / "index.html"

    class Handler(BaseHTTPRequestHandler):
        server_version = "JournalFactoryOrchestrator/1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_GET(self) -> None:
            if self.path == "/":
                self._write_html(page_path.read_bytes())
                return
            if self.path == "/api/orchestrator/state":
                self._write_json(HTTPStatus.OK, app.state())
                return
            if self.path == "/health":
                self._write_json(HTTPStatus.OK, {"status": "ok"})
                return
            self._write_json(
                HTTPStatus.NOT_FOUND,
                {"error": {"code": "HTTP_NOT_FOUND", "message": "Route not found.", "details": {}}},
            )

        def do_POST(self) -> None:
            if self.path != "/api/orchestrator/start":
                self._write_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": {"code": "HTTP_NOT_FOUND", "message": "Route not found.", "details": {}}},
                )
                return
            try:
                body = self._read_json()
            except ValueError:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": {"code": "HTTP_JSON_INVALID", "message": "Request body must be a JSON object.", "details": {}}},
                )
                return

            run_id = body.get("run_id")
            if run_id is not None and not isinstance(run_id, str):
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": {"code": "RUN_ID_INVALID", "message": "run_id must be a string.", "details": {}}},
                )
                return
            try:
                self._write_json(HTTPStatus.OK, app.start(run_id))
            except OrchestratorError as error:
                self._write_json(HTTPStatus.CONFLICT, {"error": error.to_dict()})

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_048_576:
                raise ValueError("body too large")
            raw = self.rfile.read(length) if length else b"{}"
            value = json.loads(raw.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError("body is not an object")
            return value

        def _write_html(self, body: bytes) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(body)

        def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Journal Factory Orchestrator menu.")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = make_server("127.0.0.1", args.port)
    host, port = server.server_address
    print(f"Journal Factory Orchestrator: http://{host}:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
