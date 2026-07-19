from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol

from .models import (
    CandidateSet,
    CoreEvent,
    DashboardFailure,
    DashboardSnapshot,
    DiscoveryResult,
    OrchestrationResult,
    StartRunRequest,
    WorkflowSubmission,
    WorkspaceRun,
)


class DashboardPortError(Exception):
    """Typed failure raised by an adapter implementing a Dashboard port."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        retryable: bool,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = dict(details or {})


class DashboardOperationError(Exception):
    """Browser-safe application failure with an optional persisted snapshot."""

    def __init__(
        self,
        *,
        failure: DashboardFailure,
        snapshot: DashboardSnapshot | None = None,
    ) -> None:
        super().__init__(f"{failure.code}: {failure.message}")
        self.failure = failure
        self.snapshot = snapshot


class WorkspaceDriverPort(Protocol):
    def create_or_restore(self, request: StartRunRequest) -> WorkspaceRun: ...

    def restore(self, run_id: str) -> WorkspaceRun: ...


class SourceDiscoveryPort(Protocol):
    def discover(
        self,
        workspace: WorkspaceRun,
        *,
        recursive: bool,
    ) -> DiscoveryResult: ...


class ExcelCandidateLocatorPort(Protocol):
    def locate(self, discovery: DiscoveryResult) -> CandidateSet: ...


class ArticleCandidateLocatorPort(Protocol):
    def locate(self, discovery: DiscoveryResult) -> CandidateSet: ...


EventSink = Callable[[CoreEvent], None]


class OrchestratorPort(Protocol):
    def submit(
        self,
        submission: WorkflowSubmission,
        event_sink: EventSink,
    ) -> OrchestrationResult: ...

    def resume(
        self,
        run_id: str,
        event_sink: EventSink,
    ) -> OrchestrationResult: ...


class DashboardStateStorePort(Protocol):
    def save(self, snapshot: DashboardSnapshot) -> None: ...

    def load(self, run_id: str) -> DashboardSnapshot | None: ...


class DashboardBackendPort(Protocol):
    def start_run(self, request: StartRunRequest) -> DashboardSnapshot: ...

    def resume_run(self, run_id: str) -> DashboardSnapshot: ...

    def get_run(self, run_id: str) -> DashboardSnapshot: ...
