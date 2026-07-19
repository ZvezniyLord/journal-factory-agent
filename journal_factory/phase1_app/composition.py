from __future__ import annotations

from pathlib import Path

from journal_factory.dashboard_core.service import DashboardService
from journal_factory.workspace_driver.adapters import LocalFileSystemAdapter, SystemClock
from journal_factory.workspace_driver.driver import WorkspaceDriver

from .adapters import (
    DashboardOrchestratorAdapter,
    EmptyCandidateLocator,
    NativeSelectionAdapter,
    SelectedSourceAdapter,
    WorkspaceDashboardAdapter,
    WorkspaceDashboardStateStore,
)
from .application import Phase1Application, SelectionPort


def build_application(
    *,
    desktop_path: str | Path,
    state_directory: str | Path,
    dialog: SelectionPort | None = None,
) -> Phase1Application:
    filesystem = LocalFileSystemAdapter()
    clock = SystemClock()
    workspace_driver = WorkspaceDriver(
        filesystem=filesystem,
        desktop_path=desktop_path,
        state_directory=state_directory,
        clock=clock,
    )
    dashboard = DashboardService(
        workspace_driver=WorkspaceDashboardAdapter(workspace_driver),
        source_discovery=SelectedSourceAdapter(),
        excel_candidate_locator=EmptyCandidateLocator("excel"),
        article_candidate_locator=EmptyCandidateLocator("article"),
        orchestrator=DashboardOrchestratorAdapter(workspace_driver, clock),
        state_store=WorkspaceDashboardStateStore(workspace_driver),
        clock=lambda: clock.now().isoformat().replace("+00:00", "Z"),
    )
    return Phase1Application(
        workspace_driver=workspace_driver,
        dashboard=dashboard,
        dialog=dialog or NativeSelectionAdapter(),
    )
