from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from journal_factory.dashboard_core.models import (
    CandidateRecord,
    CandidateSet,
    CoreEvent,
    CoreState,
    DashboardSnapshot,
    DiscoveredFile,
    DiscoveryResult,
    FileRecord,
    FinalResult,
    OrchestrationResult,
    ReportRecord,
    StartRunRequest,
    WarningRecord,
    WorkflowSubmission,
    WorkspaceRun,
)
from journal_factory.dashboard_core.ports import DashboardPortError


class FixedClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 7, 19, 20, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        value = self._value
        self._value += timedelta(seconds=1)
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")


class MemoryStateStore:
    def __init__(self) -> None:
        self.snapshots: dict[str, DashboardSnapshot] = {}
        self.history: list[DashboardSnapshot] = []
        self.fail_save = False
        self.fail_load = False

    def save(self, snapshot: DashboardSnapshot) -> None:
        if self.fail_save:
            raise DashboardPortError(
                code="TEST_STATE_SAVE_FAILED",
                message="Deterministic state save failure",
                retryable=True,
            )
        self.snapshots[snapshot.run_id] = snapshot
        self.history.append(snapshot)

    def load(self, run_id: str) -> DashboardSnapshot | None:
        if self.fail_load:
            raise DashboardPortError(
                code="TEST_STATE_LOAD_FAILED",
                message="Deterministic state load failure",
                retryable=False,
            )
        return self.snapshots.get(run_id)


class DeterministicWorkspaceAdapter:
    def __init__(self) -> None:
        self.create_requests: list[StartRunRequest] = []
        self.restore_requests: list[str] = []
        self.runs: dict[str, WorkspaceRun] = {}
        self.failure: DashboardPortError | None = None

    def create_or_restore(self, request: StartRunRequest) -> WorkspaceRun:
        self.create_requests.append(request)
        if self.failure:
            raise self.failure
        run = WorkspaceRun(
            run_id=f"run-{request.journal_number}",
            journal_number=request.journal_number,
            source_folder=request.source_folder,
            output_folder=request.output_folder,
        )
        self.runs[run.run_id] = run
        return run

    def restore(self, run_id: str) -> WorkspaceRun:
        self.restore_requests.append(run_id)
        if self.failure:
            raise self.failure
        if run_id not in self.runs:
            raise DashboardPortError(
                code="TEST_RUN_NOT_FOUND",
                message="Deterministic workspace run was not found",
                retryable=False,
            )
        return self.runs[run_id]


class RecursiveDiscoveryAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple[WorkspaceRun, bool]] = []
        self.failure: DashboardPortError | None = None

    def discover(
        self,
        workspace: WorkspaceRun,
        *,
        recursive: bool,
    ) -> DiscoveryResult:
        self.calls.append((workspace, recursive))
        if self.failure:
            raise self.failure
        root = Path(workspace.source_folder)
        iterator = root.rglob("*") if recursive else root.glob("*")
        paths = sorted(path for path in iterator if path.is_file())
        files = tuple(
            DiscoveredFile(
                file_id=path.relative_to(root).as_posix(),
                display_name=path.name,
                reference=str(path.resolve()),
            )
            for path in paths
        )
        unsupported = tuple(
            WarningRecord(
                record_id=f"unsupported:{item.file_id}",
                code="UNSUPPORTED_FILE",
                message=f"No candidate locator accepted {item.display_name}",
                producer_core="source_discovery",
            )
            for item in files
            if Path(item.display_name).suffix.lower() not in {".xlsx", ".xls", ".docx", ".doc"}
        )
        return DiscoveryResult(files=files, warnings=unsupported)


class SuffixCandidateLocator:
    def __init__(self, *, kind: str, suffixes: set[str]) -> None:
        self.kind = kind
        self.suffixes = suffixes
        self.calls: list[DiscoveryResult] = []
        self.failure: DashboardPortError | None = None

    def locate(self, discovery: DiscoveryResult) -> CandidateSet:
        self.calls.append(discovery)
        if self.failure:
            raise self.failure
        candidates = tuple(
            CandidateRecord(
                candidate_id=item.file_id,
                display_name=item.display_name,
                reference=item.reference,
            )
            for item in discovery.files
            if Path(item.display_name).suffix.lower() in self.suffixes
        )
        return CandidateSet(kind=self.kind, candidates=candidates)


class DeterministicOrchestratorAdapter:
    def __init__(self) -> None:
        warning = WarningRecord(
            record_id="orchestrator-warning",
            code="OPERATOR_REVIEW",
            message="Review the generated inventory",
            producer_core="orchestrator_core",
        )
        report = ReportRecord(
            record_id="inventory-report",
            producer_core="source_discovery",
            kind="source_inventory",
            display_name="Source inventory",
            reference="reports/source_inventory.json",
            status="complete",
            digest="sha256:inventory",
        )
        file_record = FileRecord(
            record_id="run-result",
            producer_core="orchestrator_core",
            kind="result",
            display_name="Run result",
            reference="final/run_result.json",
            status="ready",
        )
        self.events = (
            CoreEvent(
                sequence=1,
                core_id="source_discovery",
                state=CoreState.COMPLETED,
                completed_work=1,
                total_work=1,
                message="Source inventory accepted",
                warnings=(warning,),
            ),
            CoreEvent(
                sequence=2,
                core_id="orchestrator_core",
                state=CoreState.COMPLETED,
                completed_work=2,
                total_work=2,
                message="Workflow complete",
                warnings=(warning,),
                reports=(report, report),
                files=(file_record, file_record),
                final_result=FinalResult(
                    status="PASS WITH WARNINGS",
                    production_ready=False,
                    message="Deterministic adapter completed with review warning",
                ),
            ),
        )
        self.submissions: list[WorkflowSubmission] = []
        self.resume_requests: list[str] = []
        self.failure: DashboardPortError | None = None

    def submit(
        self,
        submission: WorkflowSubmission,
        event_sink: Callable[[CoreEvent], None],
    ) -> OrchestrationResult:
        self.submissions.append(submission)
        return self._emit(event_sink)

    def resume(
        self,
        run_id: str,
        event_sink: Callable[[CoreEvent], None],
    ) -> OrchestrationResult:
        self.resume_requests.append(run_id)
        return self._emit(event_sink)

    def _emit(
        self,
        event_sink: Callable[[CoreEvent], None],
    ) -> OrchestrationResult:
        if self.failure:
            raise self.failure
        for event in self.events:
            event_sink(event)
        return OrchestrationResult(final_result=self.events[-1].final_result)
