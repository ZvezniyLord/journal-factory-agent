from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from journal_factory.dashboard_core.models import (
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
from journal_factory.orchestrator_core.adapters import BootstrapCore, InMemoryActionLog
from journal_factory.orchestrator_core.contracts import CoreDescriptor, RunRequest
from journal_factory.orchestrator_core.orchestrator import Orchestrator
from journal_factory.orchestrator_core.registry import CoreRegistry
from journal_factory.workspace_driver.driver import WorkspaceDriver
from journal_factory.workspace_driver.errors import WorkspaceError
from journal_factory.workspace_driver.models import WorkspaceRequest


class NativeSelectionAdapter:
    """Opens native dialogs only when requested through the loopback API."""

    _KINDS = {"source_file", "source_folder", "output_folder"}

    def select(self, kind: str) -> str | None:
        if kind not in self._KINDS:
            raise ValueError("Unsupported selection kind")
        try:
            import tkinter
            from tkinter import filedialog

            root = tkinter.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            try:
                if kind == "source_file":
                    selected = filedialog.askopenfilename(
                        title="Select conference archive or source file",
                        filetypes=(
                            ("Conference archives", "*.zip *.7z *.rar"),
                            ("All files", "*.*"),
                        ),
                    )
                else:
                    title = (
                        "Select conference source folder"
                        if kind == "source_folder"
                        else "Select output parent folder"
                    )
                    selected = filedialog.askdirectory(title=title, mustexist=True)
            finally:
                root.destroy()
            return selected or None
        except Exception as error:
            raise RuntimeError("Native selection is unavailable.") from error


class WorkspaceDashboardAdapter:
    def __init__(self, driver: WorkspaceDriver) -> None:
        self._driver = driver

    def create_or_restore(self, request: StartRunRequest) -> WorkspaceRun:
        try:
            status = self._driver.create(
                WorkspaceRequest(
                    source_path=request.source_folder,
                    output_parent=request.output_folder,
                    journal_number=request.journal_number,
                )
            )
        except WorkspaceError as error:
            raise _dashboard_port_error(error) from None
        return WorkspaceRun(
            run_id=status.run_id,
            journal_number=status.config.journal_number,
            source_folder=str(status.config.source_path),
            output_folder=str(status.paths["workspace"]),
        )

    def restore(self, run_id: str) -> WorkspaceRun:
        try:
            status = self._driver.status(run_id)
        except WorkspaceError as error:
            raise _dashboard_port_error(error) from None
        return WorkspaceRun(
            run_id=status.run_id,
            journal_number=status.config.journal_number,
            source_folder=str(status.config.source_path),
            output_folder=str(status.paths["workspace"]),
        )


class SelectedSourceAdapter:
    """Reports only the selected Phase 1 source boundary; it does not parse it."""

    def discover(self, workspace: WorkspaceRun, *, recursive: bool) -> DiscoveryResult:
        source = Path(workspace.source_folder)
        item = DiscoveredFile(
            file_id="selected-source",
            display_name=source.name,
            reference=str(source),
        )
        warning = WarningRecord(
            record_id="phase1-source-boundary",
            code="PHASE1_SOURCE_NOT_PARSED",
            message="The source is registered but its contents are outside Phase 1.",
            producer_core="phase1_browser_acceptance",
        )
        return DiscoveryResult(files=(item,), warnings=(warning,))


class EmptyCandidateLocator:
    def __init__(self, kind: str) -> None:
        self._kind = kind

    def locate(self, discovery: DiscoveryResult) -> CandidateSet:
        return CandidateSet(kind=self._kind, candidates=())


class WorkspaceDashboardStateStore:
    def __init__(self, driver: WorkspaceDriver) -> None:
        self._driver = driver

    def save(self, snapshot: DashboardSnapshot) -> None:
        try:
            self._driver.save_dashboard_state(snapshot.run_id, snapshot.to_dict())
        except WorkspaceError as error:
            raise _dashboard_port_error(error) from None

    def load(self, run_id: str) -> DashboardSnapshot | None:
        try:
            payload = self._driver.load_dashboard_state(run_id)
            return DashboardSnapshot.from_dict(payload) if payload is not None else None
        except WorkspaceError as error:
            raise _dashboard_port_error(error) from None
        except Exception:
            raise DashboardPortError(
                code="DASHBOARD_STATE_INVALID",
                message="Persisted Dashboard state is invalid.",
                retryable=False,
            ) from None


class DashboardOrchestratorAdapter:
    """Adapts the real Orchestrator domain to Dashboard's event contract."""

    def __init__(self, driver: WorkspaceDriver, clock: Any) -> None:
        self._driver = driver
        self._clock = clock

    def submit(
        self,
        submission: WorkflowSubmission,
        event_sink: Callable[[CoreEvent], None],
    ) -> OrchestrationResult:
        run_id = submission.workspace.run_id
        registry = CoreRegistry()
        registry.register(CoreDescriptor("phase1_workspace_acceptance"), BootstrapCore())
        actions = InMemoryActionLog()
        orchestrator = Orchestrator(registry, actions, self._clock)
        orchestrator.begin(
            RunRequest(run_id=run_id, pipeline=("phase1_workspace_acceptance",))
        )
        snapshot = orchestrator.run_to_terminal()
        status = self._driver.status(run_id)
        reports = tuple(
            ReportRecord(
                record_id=f"workspace-report:{name}",
                producer_core=("dashboard_core" if name == "dashboard_state" else "workspace_driver"),
                kind=name,
                display_name=name.replace("_", " ").title(),
                reference=str(path),
                status="complete",
            )
            for name, path in status.reports.items()
        )
        files = tuple(
            FileRecord(
                record_id=f"workspace-output:{name}",
                producer_core="workspace_driver",
                kind=name,
                display_name=name.replace("_", " ").title(),
                reference=str(status.paths[name]),
                status="ready",
            )
            for name in ("workspace", "source_snapshot", "rendered_pdf", "rendered_png", "final")
        )
        final = FinalResult(
            status="PASS WITH WARNINGS",
            production_ready=False,
            message="Phase 1 workspace and local orchestration completed.",
        )
        event_sink(
            CoreEvent(
                sequence=1,
                core_id="phase1_workspace_acceptance",
                state=CoreState.COMPLETED,
                completed_work=1,
                total_work=1,
                message=f"Workspace acceptance complete ({snapshot.action_count} actions)",
            )
        )
        event_sink(
            CoreEvent(
                sequence=2,
                core_id="orchestrator_core",
                state=CoreState.COMPLETED,
                completed_work=2,
                total_work=2,
                message="Phase 1 orchestration complete",
                reports=reports,
                files=files,
                final_result=final,
            )
        )
        return OrchestrationResult(final_result=final)

    def resume(
        self,
        run_id: str,
        event_sink: Callable[[CoreEvent], None],
    ) -> OrchestrationResult:
        self._driver.status(run_id)
        return OrchestrationResult(
            final_result=FinalResult(
                status="PASS WITH WARNINGS",
                production_ready=False,
                message="The completed Phase 1 run was restored.",
            )
        )


def _dashboard_port_error(error: WorkspaceError) -> DashboardPortError:
    return DashboardPortError(
        code=error.code,
        message=error.message,
        retryable=error.status >= 500,
        details=error.details,
    )
