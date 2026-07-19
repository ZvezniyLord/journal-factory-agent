from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


def freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze_value(item) for item in value)
    return value


def freeze_mapping(value: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    return freeze_value(dict(value or {}))


def thaw_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, frozenset)):
        return [thaw_value(item) for item in value]
    return value


class RunState(str, Enum):
    IDLE = "idle"
    VALIDATING = "validating"
    RUNNING = "running"
    PAUSE_REQUESTED = "pause_requested"
    PAUSED = "paused"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"


class InvocationStatus(str, Enum):
    SUCCESS = "success"
    RETRYABLE_FAILURE = "retryable_failure"
    TERMINAL_FAILURE = "terminal_failure"


class FailureRoute(str, Enum):
    FAIL_RUN = "fail_run"
    PAUSE_RUN = "pause_run"
    CONTINUE_WITH_WARNING = "continue_with_warning"


@dataclass(frozen=True, slots=True)
class CoreDescriptor:
    core_id: str
    dependencies: tuple[str, ...] = ()
    max_retries: int = 0
    failure_route: FailureRoute = FailureRoute.FAIL_RUN
    operation: str = "run"

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependencies", tuple(self.dependencies))


@dataclass(frozen=True, slots=True)
class RunRequest:
    run_id: str
    pipeline: tuple[str, ...]
    payload_by_core: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    pre_satisfied_dependencies: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(self, "pipeline", tuple(self.pipeline))
        object.__setattr__(self, "payload_by_core", freeze_mapping(self.payload_by_core))
        object.__setattr__(
            self,
            "pre_satisfied_dependencies",
            frozenset(self.pre_satisfied_dependencies),
        )


@dataclass(frozen=True, slots=True)
class PauseRequest:
    run_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class ResumeRequest:
    run_id: str


@dataclass(frozen=True, slots=True)
class CoreInvocationRequest:
    request_id: str
    run_id: str
    core_id: str
    operation: str
    attempt: int
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", freeze_mapping(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "run_id": self.run_id,
            "core_id": self.core_id,
            "operation": self.operation,
            "attempt": self.attempt,
            "payload": thaw_value(self.payload),
        }


@dataclass(frozen=True, slots=True)
class InvocationError:
    code: str
    message: str
    retryable: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", freeze_mapping(self.details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "details": thaw_value(self.details),
        }


@dataclass(frozen=True, slots=True)
class CoreInvocationResult:
    status: InvocationStatus
    output: Mapping[str, Any] = field(default_factory=dict)
    error: InvocationError | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "output", freeze_mapping(self.output))
        if self.status is InvocationStatus.SUCCESS and self.error is not None:
            raise ValueError("A successful invocation cannot contain an error")
        if self.status is not InvocationStatus.SUCCESS and self.error is None:
            raise ValueError("A failed invocation must contain an error")

    @classmethod
    def success(cls, output: Mapping[str, Any] | None = None) -> CoreInvocationResult:
        return cls(status=InvocationStatus.SUCCESS, output=output or {})

    @classmethod
    def retryable_failure(
        cls,
        code: str,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> CoreInvocationResult:
        return cls(
            status=InvocationStatus.RETRYABLE_FAILURE,
            error=InvocationError(code, message, True, details or {}),
        )

    @classmethod
    def terminal_failure(
        cls,
        code: str,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> CoreInvocationResult:
        return cls(
            status=InvocationStatus.TERMINAL_FAILURE,
            error=InvocationError(code, message, False, details or {}),
        )


@dataclass(frozen=True, slots=True)
class ActionRecord:
    sequence: int
    timestamp_utc: str
    run_id: str | None
    core_id: str | None
    action: str
    status: str
    attempt: int | None
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", freeze_mapping(self.details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sequence": self.sequence,
            "timestamp_utc": self.timestamp_utc,
            "run_id": self.run_id,
            "core_id": self.core_id,
            "action": self.action,
            "status": self.status,
            "attempt": self.attempt,
            "message": self.message,
            "details": thaw_value(self.details),
        }


@dataclass(frozen=True, slots=True)
class RunSnapshot:
    run_id: str | None
    state: RunState
    pipeline: tuple[str, ...] = ()
    current_core: str | None = None
    next_core: str | None = None
    completed_cores: tuple[str, ...] = ()
    attempts: Mapping[str, int] = field(default_factory=dict)
    warnings: tuple[InvocationError, ...] = ()
    failure: InvocationError | None = None
    pause_reason: str | None = None
    revision: int = 0
    action_count: int = 0
    schema_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "pipeline", tuple(self.pipeline))
        object.__setattr__(self, "completed_cores", tuple(self.completed_cores))
        object.__setattr__(self, "attempts", freeze_mapping(self.attempts))
        object.__setattr__(self, "warnings", tuple(self.warnings))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "state": self.state.value,
            "pipeline": list(self.pipeline),
            "current_core": self.current_core,
            "next_core": self.next_core,
            "completed_cores": list(self.completed_cores),
            "attempts": thaw_value(self.attempts),
            "warnings": [warning.to_dict() for warning in self.warnings],
            "failure": self.failure.to_dict() if self.failure else None,
            "pause_reason": self.pause_reason,
            "revision": self.revision,
            "action_count": self.action_count,
        }


@dataclass(frozen=True, slots=True)
class LLMTaskRequest:
    task_id: str
    run_id: str
    purpose: str
    evidence_references: tuple[str, ...]
    constraints: Mapping[str, Any]
    response_schema: Mapping[str, Any]
    minimum_confidence: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_references", tuple(self.evidence_references))
        object.__setattr__(self, "constraints", freeze_mapping(self.constraints))
        object.__setattr__(self, "response_schema", freeze_mapping(self.response_schema))


@dataclass(frozen=True, slots=True)
class LLMTaskResponse:
    task_id: str
    status: str
    output: Mapping[str, Any]
    confidence: float
    provenance: Mapping[str, Any]
    validation_status: str
    warnings: tuple[str, ...] = ()
    error: InvocationError | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "output", freeze_mapping(self.output))
        object.__setattr__(self, "provenance", freeze_mapping(self.provenance))
        object.__setattr__(self, "warnings", tuple(self.warnings))
