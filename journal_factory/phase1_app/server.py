from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlparse

from journal_factory.dashboard_core.ports import DashboardOperationError
from journal_factory.workspace_driver.errors import WorkspaceError

from .application import Phase1Application, Phase1ApplicationError


_MAX_REQUEST_BYTES = 1024 * 1024


class _LoopbackServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Phase1HttpServer:
    def __init__(
        self,
        application: Phase1Application,
        *,
        index_path: str | Path,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        if host != "127.0.0.1":
            raise ValueError("Phase 1 server must bind to 127.0.0.1")
        if not 0 <= port <= 65535:
            raise ValueError("port must be between 0 and 65535")
        self._index_path = Path(index_path).resolve()
        handler = _make_handler(application, self._index_path)
        self._server = _LoopbackServer((host, port), handler)
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
            raise RuntimeError("Phase 1 server is already started")
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="journal-factory-phase1",
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
    application: Phase1Application,
    index_path: Path,
) -> type[BaseHTTPRequestHandler]:
    class Phase1RequestHandler(BaseHTTPRequestHandler):
        server_version = "JournalFactoryPhase1/1"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._serve_index()
                return
            if parsed.path == "/favicon.ico":
                self.send_response(HTTPStatus.NO_CONTENT)
                self.end_headers()
                return
            if parsed.path == "/health":
                self._write_json(HTTPStatus.OK, {"status": "ok", "phase": 1})
                return
            if parsed.path == "/api/workspace/defaults":
                self._invoke(application.defaults, HTTPStatus.OK)
                return
            if parsed.path == "/api/workspace/status":
                run_id = parse_qs(parsed.query).get("run_id", [""])[0]
                self._invoke(lambda: application.workspace_status(run_id), HTTPStatus.OK)
                return
            run_id = _parse_run_path(parsed.path)
            if run_id is not None:
                self._invoke(lambda: application.get_run(run_id), HTTPStatus.OK)
                return
            self._route_not_found()

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            routes: dict[str, tuple[Callable[[dict[str, Any]], Any], HTTPStatus]] = {
                "/api/workspace/validate": (application.validate, HTTPStatus.OK),
                "/api/workspace/create": (application.create_workspace, HTTPStatus.CREATED),
                "/api/runs/start": (application.start_run, HTTPStatus.OK),
                "/api/select": (application.select, HTTPStatus.OK),
            }
            route = routes.get(parsed.path)
            if route is not None:
                try:
                    payload = self._read_json_object()
                except _HttpFailure as error:
                    self._write_error(error.status, error.code, error.message)
                    return
                operation, success_status = route
                if parsed.path == "/api/workspace/validate":
                    self._invoke_validation(lambda: operation(payload))
                else:
                    self._invoke(lambda: operation(payload), success_status)
                return
            run_id = _parse_resume_path(parsed.path)
            if run_id is not None:
                try:
                    self._read_json_object()
                except _HttpFailure as error:
                    self._write_error(error.status, error.code, error.message)
                    return
                self._invoke(lambda: application.resume_run(run_id), HTTPStatus.OK)
                return
            self._route_not_found()

        def do_PUT(self) -> None:
            self._method_not_allowed()

        def do_PATCH(self) -> None:
            self._method_not_allowed()

        def do_DELETE(self) -> None:
            self._method_not_allowed()

        def log_message(self, format: str, *args: object) -> None:
            return

        def _serve_index(self) -> None:
            try:
                body = index_path.read_bytes()
            except OSError:
                self._write_error(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    "INDEX_UNAVAILABLE",
                    "The Journal Factory interface is unavailable.",
                )
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)

        def _invoke_validation(self, operation: Callable[[], tuple[dict[str, Any], int]]) -> None:
            try:
                body, status = operation()
            except Exception as error:
                self._handle_error(error)
                return
            self._write_json(HTTPStatus(status), body)

        def _invoke(self, operation: Callable[[], Any], success: HTTPStatus) -> None:
            try:
                body = operation()
            except Exception as error:
                self._handle_error(error)
                return
            self._write_json(success, body)

        def _handle_error(self, error: Exception) -> None:
            if isinstance(error, WorkspaceError):
                self._write_json(HTTPStatus(error.status), {"error": error.to_dict()})
                return
            if isinstance(error, Phase1ApplicationError):
                self._write_json(HTTPStatus(error.status), {"error": error.to_dict()})
                return
            if isinstance(error, DashboardOperationError):
                status = _dashboard_status(error.failure.code)
                body: dict[str, Any] = {"error": error.failure.to_dict()}
                if error.snapshot is not None:
                    body["run"] = error.snapshot.to_dict()
                self._write_json(status, body)
                return
            self._write_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "PHASE1_INTERNAL_ERROR",
                "The request could not be completed.",
            )

        def _read_json_object(self) -> dict[str, Any]:
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise _HttpFailure(HTTPStatus.BAD_REQUEST, "HTTP_JSON_REQUIRED", "A JSON body is required.")
            try:
                length = int(raw_length)
            except ValueError:
                raise _HttpFailure(HTTPStatus.BAD_REQUEST, "HTTP_JSON_INVALID", "Content-Length is invalid.") from None
            if length < 0 or length > _MAX_REQUEST_BYTES:
                raise _HttpFailure(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "HTTP_JSON_TOO_LARGE", "The JSON body is too large.")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise _HttpFailure(HTTPStatus.BAD_REQUEST, "HTTP_JSON_INVALID", "The body must be valid UTF-8 JSON.") from None
            if not isinstance(payload, dict):
                raise _HttpFailure(HTTPStatus.BAD_REQUEST, "HTTP_JSON_INVALID", "The JSON body must be an object.")
            return payload

        def _route_not_found(self) -> None:
            self._write_error(HTTPStatus.NOT_FOUND, "ROUTE_NOT_FOUND", "The requested route was not found.")

        def _method_not_allowed(self) -> None:
            self._write_error(HTTPStatus.METHOD_NOT_ALLOWED, "METHOD_NOT_ALLOWED", "The HTTP method is not supported.")

        def _write_error(self, status: HTTPStatus, code: str, message: str) -> None:
            self._write_json(status, {"error": {"code": code, "message": message, "details": {}}})

        def _write_json(self, status: HTTPStatus, payload: Any) -> None:
            body = (json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

    return Phase1RequestHandler


class _HttpFailure(Exception):
    def __init__(self, status: HTTPStatus, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _parse_run_path(path: str) -> str | None:
    prefix = "/api/runs/"
    if not path.startswith(prefix):
        return None
    tail = path[len(prefix) :]
    if not tail or "/" in tail:
        return None
    return unquote(tail)


def _parse_resume_path(path: str) -> str | None:
    prefix = "/api/runs/"
    suffix = "/resume"
    if not path.startswith(prefix) or not path.endswith(suffix):
        return None
    run_id = path[len(prefix) : -len(suffix)]
    if not run_id or "/" in run_id:
        return None
    return unquote(run_id)


def _dashboard_status(code: str) -> HTTPStatus:
    if code in {"RUN_NOT_FOUND"}:
        return HTTPStatus.NOT_FOUND
    if code in {"INVALID_DASHBOARD_REQUEST"}:
        return HTTPStatus.UNPROCESSABLE_ENTITY
    if code in {"DASHBOARD_STATE_INVALID"}:
        return HTTPStatus.CONFLICT
    if code in {"DASHBOARD_STATE_PERSISTENCE_FAILED"}:
        return HTTPStatus.SERVICE_UNAVAILABLE
    return HTTPStatus.BAD_GATEWAY
