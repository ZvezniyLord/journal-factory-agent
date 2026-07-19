from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


def _freeze_paths(values: Mapping[str, Path]) -> Mapping[str, Path]:
    return MappingProxyType(dict(values))


@dataclass(frozen=True, slots=True)
class WorkspaceRequest:
    source_path: str
    output_parent: str
    journal_number: str


@dataclass(frozen=True, slots=True)
class WorkspaceIssue:
    code: str
    message: str
    field: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {"code": self.code, "message": self.message, "field": self.field}


@dataclass(frozen=True, slots=True)
class WorkspaceConfig:
    source_path: Path
    output_parent: Path
    journal_number: str
    requested_journal_number: str


@dataclass(frozen=True, slots=True)
class WorkspaceLayout:
    paths: Mapping[str, Path]
    reports: Mapping[str, Path]

    def __post_init__(self) -> None:
        object.__setattr__(self, "paths", _freeze_paths(self.paths))
        object.__setattr__(self, "reports", _freeze_paths(self.reports))

    @classmethod
    def from_root(cls, root: Path) -> WorkspaceLayout:
        root = Path(root)
        if not root.is_absolute():
            raise ValueError("Workspace root must be absolute")
        reports = root / "reports"
        paths = {
            "workspace": root,
            "source_snapshot": root / "source_snapshot",
            "articles_raw": root / "articles_raw",
            "articles_transformed": root / "articles_transformed",
            "reports": reports,
            "logs": root / "logs",
            "database": root / "database",
            "rendered_pdf": root / "rendered" / "pdf",
            "rendered_png": root / "rendered" / "png",
            "final": root / "final",
            "temp": root / "temp",
        }
        report_paths = {
            "run_manifest": reports / "run_manifest.json",
            "action_log": reports / "action_log.jsonl",
            "path_registry": reports / "path_registry.json",
            "report_registry": reports / "report_registry.json",
            "run_summary": reports / "run_summary.html",
            "dashboard_state": reports / "dashboard_state.json",
        }
        return cls(paths=paths, reports=report_paths)


@dataclass(frozen=True, slots=True)
class RunContext:
    run_id: str
    created_at_utc: str
    updated_at_utc: str
    journal_number: str
    state: str
    mode: str = "phase1"


@dataclass(frozen=True, slots=True)
class ActionRecord:
    sequence: int
    timestamp_utc: str
    run_id: str
    core: str
    action: str
    status: str
    inputs: Mapping[str, Any] = field(default_factory=dict)
    outputs: Mapping[str, Any] = field(default_factory=dict)
    error: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "sequence": self.sequence,
            "timestamp_utc": self.timestamp_utc,
            "run_id": self.run_id,
            "core": self.core,
            "action": self.action,
            "status": self.status,
            "inputs": dict(self.inputs),
            "outputs": dict(self.outputs),
            "error": dict(self.error) if self.error is not None else None,
        }


@dataclass(frozen=True, slots=True)
class ReportRecord:
    name: str
    format: str
    producer: str
    path: Path
    status: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "format": self.format,
            "producer": self.producer,
            "path": str(self.path),
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceValidation:
    config: WorkspaceConfig | None
    workspace_path: Path | None
    errors: tuple[WorkspaceIssue, ...] = ()
    warnings: tuple[WorkspaceIssue, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors and self.config is not None

    def to_dict(self) -> dict[str, Any]:
        config = self.config
        return {
            "valid": self.valid,
            "source_path": str(config.source_path) if config else None,
            "output_parent": str(config.output_parent) if config else None,
            "journal_number": config.journal_number if config else None,
            "workspace_path": str(self.workspace_path) if self.workspace_path else None,
            "errors": [item.to_dict() for item in self.errors],
            "warnings": [item.to_dict() for item in self.warnings],
        }


@dataclass(frozen=True, slots=True)
class WorkspaceStatus:
    context: RunContext
    config: WorkspaceConfig
    layout: WorkspaceLayout
    restored: bool = False

    @property
    def run_id(self) -> str:
        return self.context.run_id

    @property
    def paths(self) -> Mapping[str, Path]:
        return self.layout.paths

    @property
    def reports(self) -> Mapping[str, Path]:
        return self.layout.reports

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "run_id": self.context.run_id,
            "state": self.context.state,
            "mode": self.context.mode,
            "created_at_utc": self.context.created_at_utc,
            "updated_at_utc": self.context.updated_at_utc,
            "journal_number": self.config.journal_number,
            "requested_journal_number": self.config.requested_journal_number,
            "source_path": str(self.config.source_path),
            "output_parent": str(self.config.output_parent),
            "workspace_path": str(self.layout.paths["workspace"]),
            "paths": {name: str(path) for name, path in self.layout.paths.items()},
            "reports": {name: str(path) for name, path in self.layout.reports.items()},
            "restored": self.restored,
        }
