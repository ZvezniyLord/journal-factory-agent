from __future__ import annotations

import hashlib
import html
import json
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Protocol

from .errors import WorkspaceError
from .models import (
    ActionRecord,
    RunContext,
    WorkspaceConfig,
    WorkspaceIssue,
    WorkspaceLayout,
    WorkspaceRequest,
    WorkspaceStatus,
    WorkspaceValidation,
)
from .ports import FileSystemAdapter
from .registries import PathRegistry, ReportRegistry


class Clock(Protocol):
    def now(self) -> datetime: ...


_INVALID_WINDOWS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_WHITESPACE = re.compile(r"\s+")
_UNDERSCORES = re.compile(r"_+")
_RUN_ID = re.compile(r"^run-[A-Za-z0-9T-]+$")
_RESERVED_WINDOWS = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class WorkspaceDriver:
    """Owns Phase 1 workspace paths, identity, persistence, and action history."""

    def __init__(
        self,
        *,
        filesystem: FileSystemAdapter,
        desktop_path: str | Path,
        state_directory: str | Path,
        clock: Clock,
    ) -> None:
        self._filesystem = filesystem
        self._desktop_path = filesystem.resolve(desktop_path)
        self._state_directory = filesystem.resolve(state_directory)
        self._clock = clock
        self._lock = threading.RLock()

    def defaults(self) -> Mapping[str, str | None]:
        return {
            "source_path": "",
            "output_parent": str(self._desktop_path),
            "journal_number": "",
            "workspace_path": None,
        }

    def validate(self, request: WorkspaceRequest) -> WorkspaceValidation:
        try:
            return self._validate(request)
        except WorkspaceError:
            raise
        except Exception:
            raise WorkspaceError(
                "FILESYSTEM_ACCESS_FAILED",
                "The selected filesystem paths could not be inspected.",
                status=503,
            ) from None

    def _validate(self, request: WorkspaceRequest) -> WorkspaceValidation:
        errors: list[WorkspaceIssue] = []
        warnings: list[WorkspaceIssue] = []

        source_text = request.source_path.strip() if isinstance(request.source_path, str) else ""
        if not source_text:
            errors.append(
                WorkspaceIssue("SOURCE_PATH_REQUIRED", "Select or enter a source archive or folder.", "source_path")
            )
            source_path = None
        else:
            source_path = self._filesystem.resolve(source_text)
            if not self._filesystem.exists(source_path):
                errors.append(
                    WorkspaceIssue("SOURCE_PATH_NOT_FOUND", "The selected source path does not exist.", "source_path")
                )
            elif not (
                self._filesystem.is_file(source_path)
                or self._filesystem.is_directory(source_path)
            ):
                errors.append(
                    WorkspaceIssue("SOURCE_PATH_UNSUPPORTED", "The selected source must be a file or directory.", "source_path")
                )

        output_text = request.output_parent.strip() if isinstance(request.output_parent, str) else ""
        output_parent = self._filesystem.resolve(output_text) if output_text else self._desktop_path
        if not self._filesystem.exists(output_parent):
            errors.append(
                WorkspaceIssue("OUTPUT_PARENT_NOT_FOUND", "The output parent does not exist.", "output_parent")
            )
        elif not self._filesystem.is_directory(output_parent):
            errors.append(
                WorkspaceIssue("OUTPUT_PARENT_NOT_DIRECTORY", "The output parent must be a directory.", "output_parent")
            )

        requested_journal = (
            request.journal_number.strip()
            if isinstance(request.journal_number, str)
            else ""
        )
        journal_number = self._sanitize_journal_number(requested_journal)
        if not requested_journal:
            errors.append(
                WorkspaceIssue("JOURNAL_NUMBER_REQUIRED", "Enter and review the journal number.", "journal_number")
            )
        elif not journal_number:
            errors.append(
                WorkspaceIssue("JOURNAL_NUMBER_INVALID", "The journal number contains no safe filename characters.", "journal_number")
            )
        elif journal_number != requested_journal:
            warnings.append(
                WorkspaceIssue(
                    "JOURNAL_NUMBER_SANITIZED",
                    f'The workspace name will use "{journal_number}".',
                    "journal_number",
                )
            )

        workspace_path = (
            self._filesystem.resolve(output_parent / journal_number)
            if journal_number
            else None
        )
        if errors:
            return WorkspaceValidation(
                config=None,
                workspace_path=workspace_path,
                errors=tuple(errors),
                warnings=tuple(warnings),
            )
        assert source_path is not None
        config = WorkspaceConfig(
            source_path=source_path,
            output_parent=output_parent,
            journal_number=journal_number,
            requested_journal_number=requested_journal,
        )
        return WorkspaceValidation(
            config=config,
            workspace_path=workspace_path,
            warnings=tuple(warnings),
        )

    def create(self, request: WorkspaceRequest) -> WorkspaceStatus:
        validation = self.validate(request)
        if not validation.valid:
            issue = validation.errors[0]
            raise WorkspaceError(
                issue.code,
                issue.message,
                status=422,
                details={"field": issue.field, "validation": validation.to_dict()},
            )
        assert validation.config is not None
        config = validation.config
        fingerprint = self._fingerprint(config)

        with self._lock:
            try:
                restored = self._restore_by_fingerprint(fingerprint)
                if restored is not None:
                    return restored
                restored = self._restore_managed_workspace(config, fingerprint)
                if restored is not None:
                    locator_payload = {
                        "run_id": restored.run_id,
                        "manifest_path": str(restored.reports["run_manifest"]),
                    }
                    self._write_json(self._run_locator(restored.run_id), locator_payload)
                    self._write_json(self._fingerprint_locator(fingerprint), locator_payload)
                    return restored
                return self._create_new(config, fingerprint)
            except WorkspaceError:
                raise
            except Exception:
                raise WorkspaceError(
                    "WORKSPACE_CREATE_FAILED",
                    "The workspace could not be created. No source file was modified.",
                    status=500,
                ) from None

    def status(self, run_id: str) -> WorkspaceStatus:
        if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
            raise WorkspaceError("RUN_ID_INVALID", "The run ID is invalid.", status=400)
        locator = self._run_locator(run_id)
        if not self._filesystem.exists(locator):
            raise WorkspaceError("RUN_NOT_FOUND", "The requested workspace run was not found.", status=404)
        try:
            pointer = self._read_json(locator)
            return self._load_manifest(
                self._filesystem.resolve(str(pointer["manifest_path"])),
                restored=True,
            )
        except WorkspaceError:
            raise
        except Exception:
            raise WorkspaceError(
                "RUN_STATE_INVALID",
                "The persisted workspace state is invalid.",
                status=409,
            ) from None

    def save_dashboard_state(self, run_id: str, payload: Mapping[str, Any]) -> None:
        with self._lock:
            try:
                status = self.status(run_id)
                destination = status.reports["dashboard_state"]
                self._write_json(destination, dict(payload))
                registry_path = status.reports["report_registry"]
                registry = self._read_json(registry_path)
                registry["reports"]["dashboard_state"]["status"] = "complete"
                self._write_json(registry_path, registry)
                self._update_manifest_state(status, str(payload.get("state", status.context.state)))
                self._append_action(
                    status,
                    action="dashboard_state_persisted",
                    outputs={"path": str(destination), "revision": payload.get("revision")},
                )
            except WorkspaceError:
                raise
            except Exception:
                raise WorkspaceError(
                    "DASHBOARD_STATE_PERSISTENCE_FAILED",
                    "Dashboard state could not be persisted in the workspace.",
                    status=503,
                ) from None

    def load_dashboard_state(self, run_id: str) -> Mapping[str, Any] | None:
        status = self.status(run_id)
        source = status.reports["dashboard_state"]
        if not self._filesystem.exists(source):
            return None
        try:
            return self._read_json(source)
        except Exception:
            raise WorkspaceError(
                "DASHBOARD_STATE_INVALID",
                "The persisted Dashboard state is invalid.",
                status=409,
            ) from None

    def _create_new(self, config: WorkspaceConfig, fingerprint: str) -> WorkspaceStatus:
        created_at = self._timestamp()
        time_token = re.sub(r"[^A-Za-z0-9T]", "", created_at)
        run_id = f"run-{time_token}-{fingerprint[:8]}"
        proposed = self._filesystem.resolve(config.output_parent / config.journal_number)
        workspace_root = self._allocate_workspace(proposed, run_id, fingerprint)
        layout = WorkspaceLayout.from_root(workspace_root)
        path_registry = PathRegistry.from_layout(layout)
        report_registry = ReportRegistry.from_layout(layout)
        actions: list[ActionRecord] = []

        for name, path in layout.paths.items():
            self._filesystem.make_directory(path)
            actions.append(
                self._action(
                    actions,
                    run_id,
                    "directory_created",
                    inputs={"path_key": name},
                    outputs={"path": str(path)},
                )
            )
        for name, report in report_registry.reports.items():
            actions.append(
                self._action(
                    actions,
                    run_id,
                    "report_registered",
                    inputs={"report": name, "format": report.format},
                    outputs={"path": str(report.path)},
                )
            )

        context = RunContext(
            run_id=run_id,
            created_at_utc=created_at,
            updated_at_utc=created_at,
            journal_number=config.journal_number,
            state="workspace_created",
        )
        manifest = self._manifest_payload(context, config, layout, fingerprint)
        path_payload = {
            "schema_version": 1,
            "run_id": run_id,
            "paths": path_registry.to_dict(),
        }
        report_payload = {
            "schema_version": 1,
            "run_id": run_id,
            "reports": report_registry.to_dict(),
        }
        summary = self._summary_html(context, config, layout)

        for name, payload in (
            ("run_manifest", manifest),
            ("path_registry", path_payload),
            ("report_registry", report_payload),
        ):
            self._write_json(layout.reports[name], payload)
            actions.append(
                self._action(
                    actions,
                    run_id,
                    "report_written",
                    inputs={"report": name},
                    outputs={"path": str(layout.reports[name])},
                )
            )
        self._filesystem.write_text(layout.reports["run_summary"], summary)
        actions.append(
            self._action(
                actions,
                run_id,
                "report_written",
                inputs={"report": "run_summary"},
                outputs={"path": str(layout.reports["run_summary"])},
            )
        )
        actions.append(
            self._action(
                actions,
                run_id,
                "report_written",
                inputs={"report": "action_log"},
                outputs={"path": str(layout.reports["action_log"])},
            )
        )
        action_text = "".join(self._json_line(record.to_dict()) for record in actions)
        self._filesystem.write_text(layout.reports["action_log"], action_text)

        locator_payload = {"run_id": run_id, "manifest_path": str(layout.reports["run_manifest"])}
        self._write_json(self._run_locator(run_id), locator_payload)
        self._write_json(self._fingerprint_locator(fingerprint), locator_payload)
        return WorkspaceStatus(context=context, config=config, layout=layout)

    def _restore_by_fingerprint(self, fingerprint: str) -> WorkspaceStatus | None:
        locator = self._fingerprint_locator(fingerprint)
        if not self._filesystem.exists(locator):
            return None
        try:
            pointer = self._read_json(locator)
            manifest_path = self._filesystem.resolve(str(pointer["manifest_path"]))
            if not self._filesystem.exists(manifest_path):
                return None
            return self._load_manifest(manifest_path, restored=True)
        except Exception:
            return None

    def _restore_managed_workspace(
        self,
        config: WorkspaceConfig,
        fingerprint: str,
    ) -> WorkspaceStatus | None:
        proposed = self._filesystem.resolve(config.output_parent / config.journal_number)
        manifest_path = WorkspaceLayout.from_root(proposed).reports["run_manifest"]
        if not self._filesystem.exists(manifest_path):
            return None
        try:
            manifest = self._read_json(manifest_path)
            if manifest.get("config_fingerprint") != fingerprint:
                return None
            return self._load_manifest(manifest_path, restored=True)
        except Exception:
            return None

    def _load_manifest(self, manifest_path: Path, *, restored: bool) -> WorkspaceStatus:
        manifest = self._read_json(manifest_path)
        root = self._filesystem.resolve(str(manifest["workspace_path"]))
        layout = WorkspaceLayout.from_root(root)
        config = WorkspaceConfig(
            source_path=self._filesystem.resolve(str(manifest["source_path"])),
            output_parent=self._filesystem.resolve(str(manifest["output_parent"])),
            journal_number=str(manifest["journal_number"]),
            requested_journal_number=str(manifest.get("requested_journal_number", manifest["journal_number"])),
        )
        context = RunContext(
            run_id=str(manifest["run_id"]),
            created_at_utc=str(manifest["created_at_utc"]),
            updated_at_utc=str(manifest["updated_at_utc"]),
            journal_number=config.journal_number,
            state=str(manifest["state"]),
            mode=str(manifest.get("mode", "phase1")),
        )
        return WorkspaceStatus(context=context, config=config, layout=layout, restored=restored)

    def _allocate_workspace(self, proposed: Path, run_id: str, fingerprint: str) -> Path:
        if not self._filesystem.exists(proposed):
            return proposed
        manifest_path = WorkspaceLayout.from_root(proposed).reports["run_manifest"]
        if self._filesystem.exists(manifest_path):
            try:
                manifest = self._read_json(manifest_path)
                if manifest.get("config_fingerprint") == fingerprint:
                    return proposed
            except Exception:
                pass
        candidate = proposed.parent / f"{proposed.name}_{run_id}"
        suffix = 2
        while self._filesystem.exists(candidate):
            candidate = proposed.parent / f"{proposed.name}_{run_id}-{suffix}"
            suffix += 1
        return self._filesystem.resolve(candidate)

    def _manifest_payload(
        self,
        context: RunContext,
        config: WorkspaceConfig,
        layout: WorkspaceLayout,
        fingerprint: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "run_id": context.run_id,
            "mode": context.mode,
            "state": context.state,
            "created_at_utc": context.created_at_utc,
            "updated_at_utc": context.updated_at_utc,
            "journal_number": config.journal_number,
            "requested_journal_number": config.requested_journal_number,
            "source_path": str(config.source_path),
            "output_parent": str(config.output_parent),
            "workspace_path": str(layout.paths["workspace"]),
            "config_fingerprint": fingerprint,
            "path_registry": str(layout.reports["path_registry"]),
            "report_registry": str(layout.reports["report_registry"]),
            "action_log": str(layout.reports["action_log"]),
            "run_summary": str(layout.reports["run_summary"]),
            "dashboard_state": str(layout.reports["dashboard_state"]),
        }

    def _update_manifest_state(self, status: WorkspaceStatus, state: str) -> None:
        manifest_path = status.reports["run_manifest"]
        manifest = self._read_json(manifest_path)
        manifest["state"] = state
        manifest["updated_at_utc"] = self._timestamp()
        self._write_json(manifest_path, manifest)

    def _append_action(
        self,
        status: WorkspaceStatus,
        *,
        action: str,
        inputs: Mapping[str, Any] | None = None,
        outputs: Mapping[str, Any] | None = None,
    ) -> None:
        path = status.reports["action_log"]
        existing = self._filesystem.read_text(path).splitlines()
        record = ActionRecord(
            sequence=len(existing) + 1,
            timestamp_utc=self._timestamp(),
            run_id=status.run_id,
            core="workspace_driver",
            action=action,
            status="success",
            inputs=inputs or {},
            outputs=outputs or {},
        )
        self._filesystem.append_text(path, self._json_line(record.to_dict()))

    def _action(
        self,
        actions: list[ActionRecord],
        run_id: str,
        action: str,
        *,
        inputs: Mapping[str, Any],
        outputs: Mapping[str, Any],
    ) -> ActionRecord:
        return ActionRecord(
            sequence=len(actions) + 1,
            timestamp_utc=self._timestamp(),
            run_id=run_id,
            core="workspace_driver",
            action=action,
            status="success",
            inputs=inputs,
            outputs=outputs,
        )

    def _summary_html(
        self,
        context: RunContext,
        config: WorkspaceConfig,
        layout: WorkspaceLayout,
    ) -> str:
        rows = "".join(
            f"<tr><th>{html.escape(name)}</th><td>{html.escape(str(path))}</td></tr>"
            for name, path in layout.paths.items()
        )
        return (
            "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
            "<title>Journal Factory run summary</title>"
            "<style>body{font:14px system-ui;margin:32px;color:#1b2521}"
            "table{border-collapse:collapse;width:100%}th,td{padding:8px;border:1px solid #ccd4cf;text-align:left}</style>"
            f"<h1>Journal Factory {html.escape(config.journal_number)}</h1>"
            f"<p>Run {html.escape(context.run_id)} | {html.escape(context.state)}</p>"
            f"<p>Source: {html.escape(str(config.source_path))}</p><table>{rows}</table></html>\n"
        )

    def _sanitize_journal_number(self, value: str) -> str:
        safe = _INVALID_WINDOWS.sub("_", value.strip())
        safe = _WHITESPACE.sub("_", safe)
        safe = _UNDERSCORES.sub("_", safe).strip(" ._")
        if safe.upper() in _RESERVED_WINDOWS:
            safe = f"_{safe}"
        return safe[:80].rstrip(" ._")

    def _fingerprint(self, config: WorkspaceConfig) -> str:
        material = "\n".join(
            (str(config.source_path), str(config.output_parent), config.journal_number)
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def _run_locator(self, run_id: str) -> Path:
        digest = hashlib.sha256(run_id.encode("utf-8")).hexdigest()
        return self._state_directory / "runs" / f"{digest}.json"

    def _fingerprint_locator(self, fingerprint: str) -> Path:
        return self._state_directory / "configs" / f"{fingerprint}.json"

    def _timestamp(self) -> str:
        return self._clock.now().isoformat().replace("+00:00", "Z")

    def _read_json(self, path: Path) -> dict[str, Any]:
        payload = json.loads(self._filesystem.read_text(path))
        if not isinstance(payload, dict):
            raise ValueError("JSON object required")
        return payload

    def _write_json(self, path: Path, payload: Mapping[str, Any]) -> None:
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        self._filesystem.write_text(path, text)

    def _json_line(self, payload: Mapping[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
