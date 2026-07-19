from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .contracts import (
    ActionRecord,
    CoreInvocationRequest,
    CoreInvocationResult,
    LLMTaskRequest,
    LLMTaskResponse,
    PauseRequest,
    ResumeRequest,
    RunRequest,
    RunSnapshot,
)


class CoreInvocationPort(Protocol):
    def invoke(self, request: CoreInvocationRequest) -> CoreInvocationResult: ...


class ActionLogPort(Protocol):
    def append(self, record: ActionRecord) -> None: ...


class ClockPort(Protocol):
    def now(self) -> datetime: ...


class OrchestratorPort(Protocol):
    def begin(self, request: RunRequest) -> RunSnapshot: ...

    def advance(self) -> RunSnapshot: ...

    def request_pause(self, request: PauseRequest) -> RunSnapshot: ...

    def resume(self, request: ResumeRequest) -> RunSnapshot: ...

    def snapshot(self) -> RunSnapshot: ...


class LLMCorePort(Protocol):
    def decide(self, request: LLMTaskRequest) -> LLMTaskResponse: ...
