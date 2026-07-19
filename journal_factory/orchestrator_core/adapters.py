from __future__ import annotations

from datetime import datetime, timezone

from .contracts import ActionRecord, CoreInvocationRequest, CoreInvocationResult


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class InMemoryActionLog:
    def __init__(self) -> None:
        self._records: list[ActionRecord] = []

    def append(self, record: ActionRecord) -> None:
        expected = len(self._records) + 1
        if record.sequence != expected:
            raise ValueError(f"Expected action sequence {expected}")
        self._records.append(record)

    @property
    def records(self) -> tuple[ActionRecord, ...]:
        return tuple(self._records)


class BootstrapCore:
    def invoke(self, request: CoreInvocationRequest) -> CoreInvocationResult:
        return CoreInvocationResult.success(
            {"accepted": True, "operation": request.operation}
        )
