from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping


class RunState(str, Enum):
    CREATING = "creating"
    DISCOVERING = "discovering"
    LOCATING_CANDIDATES = "locating_candidates"
    SUBMITTING = "submitting"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    SUCCEEDED_WITH_WARNINGS = "succeeded_with_warnings"
    FAILED = "failed"


class CoreState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    WARNING = "warning"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass(frozen=True, slots=True)
class StartRunRequest:
    source_folder: str
    output_folder: str
    journal_number: str


@dataclass(frozen=True, slots=True)
class WorkspaceRun:
    run_id: str
    journal_number: str
    source_folder: str
    output_folder: str

    def __post_init__(self) -> None:
        _require_text(self.run_id, "run_id")
        _require_text(self.journal_number, "journal_number")
        _require_text(self.source_folder, "source_folder")
        _require_text(self.output_folder, "output_folder")


@dataclass(frozen=True, slots=True)
class DiscoveredFile:
    file_id: str
    display_name: str
    reference: str

    def __post_init__(self) -> None:
        _require_text(self.file_id, "file_id")
        _require_text(self.display_name, "display_name")
        _require_text(self.reference, "reference")


@dataclass(frozen=True, slots=True)
class WarningRecord:
    record_id: str
    code: str
    message: str
    producer_core: str

    def __post_init__(self) -> None:
        _require_record_fields(
            self.record_id,
            self.code,
            self.message,
            self.producer_core,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "code": self.code,
            "message": self.message,
            "producer_core": self.producer_core,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WarningRecord:
        return cls(
            record_id=str(data["record_id"]),
            code=str(data["code"]),
            message=str(data["message"]),
            producer_core=str(data["producer_core"]),
        )


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    files: tuple[DiscoveredFile, ...]
    warnings: tuple[WarningRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    candidate_id: str
    display_name: str
    reference: str

    def __post_init__(self) -> None:
        _require_text(self.candidate_id, "candidate_id")
        _require_text(self.display_name, "display_name")
        _require_text(self.reference, "reference")


@dataclass(frozen=True, slots=True)
class CandidateSet:
    kind: str
    candidates: tuple[CandidateRecord, ...]
    warnings: tuple[WarningRecord, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.kind, "kind")


@dataclass(frozen=True, slots=True)
class ReportRecord:
    record_id: str
    producer_core: str
    kind: str
    display_name: str
    reference: str
    status: str
    digest: str | None = None

    def __post_init__(self) -> None:
        _require_record_fields(
            self.record_id,
            self.producer_core,
            self.kind,
            self.display_name,
            self.reference,
            self.status,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "producer_core": self.producer_core,
            "kind": self.kind,
            "display_name": self.display_name,
            "reference": self.reference,
            "status": self.status,
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ReportRecord:
        return cls(
            record_id=str(data["record_id"]),
            producer_core=str(data["producer_core"]),
            kind=str(data["kind"]),
            display_name=str(data["display_name"]),
            reference=str(data["reference"]),
            status=str(data["status"]),
            digest=_optional_text(data.get("digest")),
        )


@dataclass(frozen=True, slots=True)
class FileRecord:
    record_id: str
    producer_core: str
    kind: str
    display_name: str
    reference: str
    status: str
    digest: str | None = None

    def __post_init__(self) -> None:
        _require_record_fields(
            self.record_id,
            self.producer_core,
            self.kind,
            self.display_name,
            self.reference,
            self.status,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "producer_core": self.producer_core,
            "kind": self.kind,
            "display_name": self.display_name,
            "reference": self.reference,
            "status": self.status,
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FileRecord:
        return cls(
            record_id=str(data["record_id"]),
            producer_core=str(data["producer_core"]),
            kind=str(data["kind"]),
            display_name=str(data["display_name"]),
            reference=str(data["reference"]),
            status=str(data["status"]),
            digest=_optional_text(data.get("digest")),
        )


@dataclass(frozen=True, slots=True)
class FinalResult:
    status: str
    production_ready: bool
    message: str

    def __post_init__(self) -> None:
        _require_text(self.status, "status")
        _require_text(self.message, "message")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "production_ready": self.production_ready,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FinalResult:
        return cls(
            status=str(data["status"]),
            production_ready=_strict_bool(
                data["production_ready"],
                "production_ready",
            ),
            message=str(data["message"]),
        )


@dataclass(frozen=True, slots=True)
class DashboardFailure:
    code: str
    message: str
    stage: str
    retryable: bool
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_record_fields(self.code, self.message, self.stage)
        object.__setattr__(self, "details", dict(self.details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "stage": self.stage,
            "retryable": self.retryable,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DashboardFailure:
        details = data.get("details", {})
        if not isinstance(details, Mapping):
            raise ValueError("failure details must be an object")
        return cls(
            code=str(data["code"]),
            message=str(data["message"]),
            stage=str(data["stage"]),
            retryable=_strict_bool(data["retryable"], "retryable"),
            details=dict(details),
        )


@dataclass(frozen=True, slots=True)
class CoreProjection:
    core_id: str
    state: CoreState
    completed_work: int
    total_work: int
    message: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.core_id, "core_id")
        _validate_progress(self.completed_work, self.total_work)

    def to_dict(self) -> dict[str, Any]:
        return {
            "core_id": self.core_id,
            "state": self.state.value,
            "completed_work": self.completed_work,
            "total_work": self.total_work,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CoreProjection:
        return cls(
            core_id=str(data["core_id"]),
            state=CoreState(str(data["state"])),
            completed_work=int(data["completed_work"]),
            total_work=int(data["total_work"]),
            message=_optional_text(data.get("message")),
        )


@dataclass(frozen=True, slots=True)
class CoreEvent:
    sequence: int
    core_id: str
    state: CoreState
    completed_work: int
    total_work: int
    message: str | None = None
    warnings: tuple[WarningRecord, ...] = ()
    reports: tuple[ReportRecord, ...] = ()
    files: tuple[FileRecord, ...] = ()
    final_result: FinalResult | None = None

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise ValueError("event sequence must be non-negative")
        _require_text(self.core_id, "core_id")
        _validate_progress(self.completed_work, self.total_work)

    @property
    def progress_percent(self) -> float:
        return _progress_percent(self.completed_work, self.total_work)


@dataclass(frozen=True, slots=True)
class WorkflowSubmission:
    workspace: WorkspaceRun
    discovery: DiscoveryResult
    excel_candidates: CandidateSet
    article_candidates: CandidateSet


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    final_result: FinalResult


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    schema_version: int
    revision: int
    run_id: str
    journal_number: str
    state: RunState
    stage: str
    source_folder: str
    output_folder: str
    created_at: str
    updated_at: str
    last_event_sequence: int
    completed_work: int
    total_work: int
    discovered_file_count: int
    excel_candidate_count: int
    article_candidate_count: int
    cores: tuple[CoreProjection, ...] = ()
    warnings: tuple[WarningRecord, ...] = ()
    reports: tuple[ReportRecord, ...] = ()
    files: tuple[FileRecord, ...] = ()
    final_result: FinalResult | None = None
    failure: DashboardFailure | None = None

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported dashboard schema version")
        if self.revision < 0:
            raise ValueError("revision must be non-negative")
        _require_record_fields(
            self.run_id,
            self.journal_number,
            self.stage,
            self.source_folder,
            self.output_folder,
            self.created_at,
            self.updated_at,
        )
        if self.last_event_sequence < 0:
            raise ValueError("last event sequence must be non-negative")
        _validate_progress(self.completed_work, self.total_work)
        for name, value in (
            ("discovered_file_count", self.discovered_file_count),
            ("excel_candidate_count", self.excel_candidate_count),
            ("article_candidate_count", self.article_candidate_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.state in {
            RunState.SUCCEEDED,
            RunState.SUCCEEDED_WITH_WARNINGS,
        } and self.final_result is None:
            raise ValueError("successful state requires an explicit final result")
        if self.state is RunState.FAILED and self.failure is None:
            raise ValueError("failed state requires a structured failure")

    @property
    def progress_percent(self) -> float:
        return _progress_percent(self.completed_work, self.total_work)

    @classmethod
    def empty(
        cls,
        *,
        run_id: str,
        journal_number: str,
        source_folder: str,
        output_folder: str,
        timestamp: str,
    ) -> DashboardSnapshot:
        return cls(
            schema_version=1,
            revision=0,
            run_id=run_id,
            journal_number=journal_number,
            state=RunState.CREATING,
            stage="workspace",
            source_folder=source_folder,
            output_folder=output_folder,
            created_at=timestamp,
            updated_at=timestamp,
            last_event_sequence=0,
            completed_work=0,
            total_work=0,
            discovered_file_count=0,
            excel_candidate_count=0,
            article_candidate_count=0,
        )

    def evolve(self, **changes: Any) -> DashboardSnapshot:
        changes.setdefault("revision", self.revision + 1)
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "revision": self.revision,
            "run_id": self.run_id,
            "journal_number": self.journal_number,
            "state": self.state.value,
            "stage": self.stage,
            "source_folder": self.source_folder,
            "output_folder": self.output_folder,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_event_sequence": self.last_event_sequence,
            "completed_work": self.completed_work,
            "total_work": self.total_work,
            "progress_percent": self.progress_percent,
            "discovered_file_count": self.discovered_file_count,
            "excel_candidate_count": self.excel_candidate_count,
            "article_candidate_count": self.article_candidate_count,
            "cores": [item.to_dict() for item in self.cores],
            "warnings": [item.to_dict() for item in self.warnings],
            "reports": [item.to_dict() for item in self.reports],
            "files": [item.to_dict() for item in self.files],
            "final_result": (
                self.final_result.to_dict() if self.final_result else None
            ),
            "failure": self.failure.to_dict() if self.failure else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DashboardSnapshot:
        final_data = data.get("final_result")
        failure_data = data.get("failure")
        return cls(
            schema_version=int(data["schema_version"]),
            revision=int(data["revision"]),
            run_id=str(data["run_id"]),
            journal_number=str(data["journal_number"]),
            state=RunState(str(data["state"])),
            stage=str(data["stage"]),
            source_folder=str(data["source_folder"]),
            output_folder=str(data["output_folder"]),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            last_event_sequence=int(data["last_event_sequence"]),
            completed_work=int(data["completed_work"]),
            total_work=int(data["total_work"]),
            discovered_file_count=int(data["discovered_file_count"]),
            excel_candidate_count=int(data["excel_candidate_count"]),
            article_candidate_count=int(data["article_candidate_count"]),
            cores=tuple(
                CoreProjection.from_dict(item) for item in data.get("cores", [])
            ),
            warnings=tuple(
                WarningRecord.from_dict(item) for item in data.get("warnings", [])
            ),
            reports=tuple(
                ReportRecord.from_dict(item) for item in data.get("reports", [])
            ),
            files=tuple(
                FileRecord.from_dict(item) for item in data.get("files", [])
            ),
            final_result=(
                FinalResult.from_dict(final_data)
                if isinstance(final_data, Mapping)
                else None
            ),
            failure=(
                DashboardFailure.from_dict(failure_data)
                if isinstance(failure_data, Mapping)
                else None
            ),
        )


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")


def _require_record_fields(*values: str) -> None:
    for index, value in enumerate(values):
        _require_text(value, f"record field {index}")


def _validate_progress(completed_work: int, total_work: int) -> None:
    if completed_work < 0 or total_work < 0:
        raise ValueError("progress values must be non-negative")
    if completed_work > total_work:
        raise ValueError("completed work cannot exceed total work")


def _progress_percent(completed_work: int, total_work: int) -> float:
    if total_work == 0:
        return 0.0
    return round(min(100.0, max(0.0, completed_work * 100.0 / total_work)), 2)


def _optional_text(value: Any) -> str | None:
    return None if value is None else str(value)


def _strict_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value
