from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping, Protocol

from journal_factory.dashboard_core.models import StartRunRequest
from journal_factory.dashboard_core.ports import DashboardBackendPort, DashboardOperationError
from journal_factory.workspace_driver.driver import WorkspaceDriver
from journal_factory.workspace_driver.errors import WorkspaceError
from journal_factory.workspace_driver.models import WorkspaceRequest, WorkspaceValidation


class SelectionPort(Protocol):
    def select(self, kind: str) -> str | None: ...


class Phase1ApplicationError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status: int,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status
        self.details = MappingProxyType(dict(details or {}))

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": dict(self.details)}


class Phase1Application:
    def __init__(
        self,
        *,
        workspace_driver: WorkspaceDriver,
        dashboard: DashboardBackendPort,
        dialog: SelectionPort,
    ) -> None:
        self._workspace_driver = workspace_driver
        self._dashboard = dashboard
        self._dialog = dialog

    def defaults(self) -> dict[str, Any]:
        return dict(self._workspace_driver.defaults())

    def validate(self, payload: Mapping[str, Any]) -> tuple[dict[str, Any], int]:
        validation = self._workspace_driver.validate(self._workspace_request(payload))
        body = {"workspace": validation.to_dict()}
        if validation.valid:
            return body, 200
        issue = validation.errors[0]
        body["error"] = {
            "code": issue.code,
            "message": issue.message,
            "details": {"field": issue.field},
        }
        return body, 422

    def create_workspace(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        status = self._workspace_driver.create(self._workspace_request(payload))
        return {"workspace": status.to_dict()}

    def workspace_status(self, run_id: str) -> dict[str, Any]:
        return {"workspace": self._workspace_driver.status(run_id).to_dict()}

    def start_run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        validation = self._workspace_driver.validate(self._workspace_request(payload))
        self._require_valid(validation)
        run_id = payload.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise Phase1ApplicationError(
                "RUN_ID_REQUIRED", "Create a workspace before starting the run.", status=422
            )
        existing = self._workspace_driver.status(run_id)
        assert validation.config is not None
        if (
            existing.config.source_path != validation.config.source_path
            or existing.config.output_parent != validation.config.output_parent
            or existing.config.journal_number != validation.config.journal_number
        ):
            raise Phase1ApplicationError(
                "RUN_CONFIG_MISMATCH",
                "The form no longer matches the created workspace. Validate and create again.",
                status=409,
            )
        snapshot = self._dashboard.start_run(
            StartRunRequest(
                source_folder=str(validation.config.source_path),
                output_folder=str(validation.config.output_parent),
                journal_number=validation.config.journal_number,
            )
        )
        workspace = self._workspace_driver.status(snapshot.run_id)
        return {"workspace": workspace.to_dict(), "run": snapshot.to_dict()}

    def get_run(self, run_id: str) -> dict[str, Any]:
        workspace = self._workspace_driver.status(run_id)
        snapshot = self._dashboard.get_run(run_id)
        return {"workspace": workspace.to_dict(), "run": snapshot.to_dict()}

    def resume_run(self, run_id: str) -> dict[str, Any]:
        workspace = self._workspace_driver.status(run_id)
        snapshot = self._dashboard.resume_run(run_id)
        return {"workspace": workspace.to_dict(), "run": snapshot.to_dict()}

    def select(self, payload: Mapping[str, Any]) -> dict[str, str]:
        kind = payload.get("kind")
        if not isinstance(kind, str) or kind not in {
            "source_file",
            "source_folder",
            "output_folder",
        }:
            raise Phase1ApplicationError(
                "SELECTION_KIND_INVALID", "The selection request is invalid.", status=400
            )
        try:
            selected = self._dialog.select(kind)
        except Exception:
            raise Phase1ApplicationError(
                "NATIVE_SELECTION_UNAVAILABLE",
                "The native selection dialog could not be opened.",
                status=503,
            ) from None
        if not selected:
            raise Phase1ApplicationError(
                "SELECTION_CANCELLED", "No path was selected.", status=409
            )
        return {"kind": kind, "path": selected}

    def _workspace_request(self, payload: Mapping[str, Any]) -> WorkspaceRequest:
        return WorkspaceRequest(
            source_path=payload.get("source_path", ""),
            output_parent=payload.get("output_parent", ""),
            journal_number=payload.get("journal_number", ""),
        )

    def _require_valid(self, validation: WorkspaceValidation) -> None:
        if validation.valid:
            return
        issue = validation.errors[0]
        raise WorkspaceError(
            issue.code,
            issue.message,
            status=422,
            details={"field": issue.field, "validation": validation.to_dict()},
        )
