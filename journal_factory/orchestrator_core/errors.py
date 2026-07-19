from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class ErrorCode(str, Enum):
    CORE_ID_INVALID = "CORE_ID_INVALID"
    CORE_ALREADY_REGISTERED = "CORE_ALREADY_REGISTERED"
    CORE_NOT_REGISTERED = "CORE_NOT_REGISTERED"
    CORE_RETRY_LIMIT_INVALID = "CORE_RETRY_LIMIT_INVALID"
    CORE_DEPENDENCY_UNKNOWN = "CORE_DEPENDENCY_UNKNOWN"
    CORE_DEPENDENCY_CYCLE = "CORE_DEPENDENCY_CYCLE"
    PIPELINE_EMPTY = "PIPELINE_EMPTY"
    PIPELINE_CORE_DUPLICATE = "PIPELINE_CORE_DUPLICATE"
    PIPELINE_DEPENDENCY_UNSATISFIED = "PIPELINE_DEPENDENCY_UNSATISFIED"
    RUN_ID_INVALID = "RUN_ID_INVALID"
    RUN_ALREADY_ACTIVE = "RUN_ALREADY_ACTIVE"
    RUN_NOT_FOUND = "RUN_NOT_FOUND"
    RUN_ID_MISMATCH = "RUN_ID_MISMATCH"
    RUN_TRANSITION_INVALID = "RUN_TRANSITION_INVALID"
    RUN_NOT_PAUSED = "RUN_NOT_PAUSED"
    CORE_RESULT_INVALID = "CORE_RESULT_INVALID"
    ACTION_LOG_WRITE_FAILED = "ACTION_LOG_WRITE_FAILED"


class OrchestratorError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = MappingProxyType(dict(details or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "message": self.message,
            "details": dict(self.details),
        }
