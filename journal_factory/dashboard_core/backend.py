from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlparse

from .models import DashboardFailure, StartRunRequest
from .ports import DashboardBackendPort, DashboardOperationError


_MAX_REQUEST_BYTES = 1024 * 1024


class _DashboardThreadingServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class DashboardHttpServer:
    def __init__(
        self,
        application: DashboardBackendPort,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        if host != "127.0.0.1":
            raise ValueError("Dashboard backend must bind to the IPv4 loopback address")
        if port < 0 or port > 65535:
            raise ValueError("port must be between 0 and 65535")
        self._application = application
        handler = _make_handler(application)
        self._server = _DashboardThreadingServer((host, port), handler)
        self._thread: threading.Thread | None = None

    @property
    def host(self) -> str:
        return str(self._server.server_address[0])

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("Dashboard backend is already started")
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="journal-factory-dashboard",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if self._thread is not None:
            self._server.shutdown()
            self._thread.join(timeout=5)
            self._thread = None
        self._server.server_close()


def _make_handler(
    application: DashboardBackendPort,
) -> type[BaseHTTPRequestHandler]:
    class DashboardRequestHandler(BaseHTTPRequestHandler):
        server_version = "JournalFactoryDashboard/1"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._write_json(HTTPStatus.OK, {"status": "ok"})
                return
            run_id = _parse_run_path(parsed.path)
            if run_id is None:
                self._route_not_found()
                return
            self._invoke(lambda: application.get_run(run_id), HTTPStatus.OK)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/dashboard/runs":
                try:
                    payload = self._read_json_object()
                    request = StartRunRequest(
                        source_folder=payload.get("source_folder"),
                        output_folder=payload.get("output_folder"),
                        journal_number=payload.get("journal_number"),
                    )
                except _RequestFailure as error:
                    self._write_failure(HTTPStatus.BAD_REQUEST, error.failure)
                    return
                self._invoke(
                    lambda: application.start_run(request),
                    HTTPStatus.CREATED,
                )
                return
            run_id = _parse_resume_path(parsed.path)
            if run_id is None:
                self._route_not_found()
                return
            try:
                self._read_json_object()
            except _RequestFailure as error:
                self._write_failure(HTTPStatus.BAD_REQUEST, error.failure)
                return
            self._invoke(lambda: application.resume_run(run_id), HTTPStatus.OK)

        def do_PUT(self) -> None:
            self._method_not_allowed()

        def do_PATCH(self) -> None:
            self._method_not_allowed()

        def do_DELETE(self) -> None:
            self._method_not_allowed()

        def log_message(self, format: str, *args: object) -> None:
            return

        def _invoke(self, operation: Any, success_status: HTTPStatus) -> None:
            try:
                snapshot = operation()
            except DashboardOperationError as error:
                body: dict[str, Any] = {"error": error.failure.to_dict()}
                if error.snapshot is not None:
                    body["run"] = error.snapshot.to_dict()
                self._write_json(_status_for_failure(error.failure), body)
                return
            except Exception:
                failure = DashboardFailure(
                    code="DASHBOARD_INTERNAL_ERROR",
                    message="The dashboard request could not be completed.",
                    stage="http_adapter",
                    retryable=False,
                )
                self._write_failure(HTTPStatus.INTERNAL_SERVER_ERROR, failure)
                return
            self._write_json(success_status, {"run": snapshot.to_dict()})

        def _read_json_object(self) -> dict[str, Any]:
            content_length = self.headers.get("Content-Length")
            if content_length is None:
                raise _invalid_request("A JSON request body is required.")
            try:
                length = int(content_length)
            except ValueError:
                raise _invalid_request("Content-Length is invalid.") from None
            if length < 0 or length > _MAX_REQUEST_BYTES:
                raise _invalid_request("The JSON request body is too large.")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise _invalid_request("The request body must be valid UTF-8 JSON.") from None
            if not isinstance(payload, dict):
                raise _invalid_request("The JSON request body must be an object.")
            return payload

        def _route_not_found(self) -> None:
            failure = DashboardFailure(
                code="ROUTE_NOT_FOUND",
                message="The requested dashboard route was not found.",
                stage="http_adapter",
                retryable=False,
            )
            self._write_failure(HTTPStatus.NOT_FOUND, failure)

        def _method_not_allowed(self) -> None:
            failure = DashboardFailure(
                code="METHOD_NOT_ALLOWED",
                message="The HTTP method is not supported for this route.",
                stage="http_adapter",
                retryable=False,
            )
            self._write_failure(HTTPStatus.METHOD_NOT_ALLOWED, failure)

        def _write_failure(
            self,
            status: HTTPStatus,
            failure: DashboardFailure,
        ) -> None:
            self._write_json(status, {"error": failure.to_dict()})

        def _write_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = (
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

    return DashboardRequestHandler


class _RequestFailure(Exception):
    def __init__(self, failure: DashboardFailure) -> None:
        super().__init__(failure.message)
        self.failure = failure


def _invalid_request(message: str) -> _RequestFailure:
    return _RequestFailure(
        DashboardFailure(
            code="INVALID_DASHBOARD_REQUEST",
            message=message,
            stage="http_adapter",
            retryable=False,
        )
    )


def _parse_run_path(path: str) -> str | None:
    prefix = "/api/dashboard/runs/"
    if not path.startswith(prefix):
        return None
    tail = path[len(prefix) :]
    if not tail or "/" in tail:
        return None
    return unquote(tail)


def _parse_resume_path(path: str) -> str | None:
    prefix = "/api/dashboard/runs/"
    suffix = "/resume"
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    encoded_run_id = path[len(prefix) : -len(suffix)]
    if not encoded_run_id or "/" in encoded_run_id:
        return None
    return unquote(encoded_run_id)


def _status_for_failure(failure: DashboardFailure) -> HTTPStatus:
    if failure.code == "INVALID_DASHBOARD_REQUEST":
        return HTTPStatus.BAD_REQUEST
    if failure.code in {"RUN_NOT_FOUND", "ROUTE_NOT_FOUND"}:
        return HTTPStatus.NOT_FOUND
    if failure.code == "DASHBOARD_STATE_INVALID":
        return HTTPStatus.CONFLICT
    if failure.code == "DASHBOARD_STATE_PERSISTENCE_FAILED":
        return HTTPStatus.SERVICE_UNAVAILABLE
    if failure.code == "DASHBOARD_INTERNAL_ERROR":
        return HTTPStatus.INTERNAL_SERVER_ERROR
    return HTTPStatus.BAD_GATEWAY
