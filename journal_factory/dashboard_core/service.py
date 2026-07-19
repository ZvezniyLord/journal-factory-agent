from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from .models import (
    CandidateSet,
    CoreEvent,
    CoreProjection,
    CoreState,
    DashboardFailure,
    DashboardSnapshot,
    DiscoveryResult,
    FileRecord,
    FinalResult,
    OrchestrationResult,
    ReportRecord,
    RunState,
    StartRunRequest,
    WarningRecord,
    WorkflowSubmission,
    WorkspaceRun,
)
from .ports import (
    ArticleCandidateLocatorPort,
    DashboardOperationError,
    DashboardPortError,
    DashboardStateStorePort,
    ExcelCandidateLocatorPort,
    OrchestratorPort,
    SourceDiscoveryPort,
    WorkspaceDriverPort,
)


RecordT = TypeVar("RecordT", WarningRecord, ReportRecord, FileRecord)


class DashboardService:
    def __init__(
        self,
        *,
        workspace_driver: WorkspaceDriverPort,
        source_discovery: SourceDiscoveryPort,
        excel_candidate_locator: ExcelCandidateLocatorPort,
        article_candidate_locator: ArticleCandidateLocatorPort,
        orchestrator: OrchestratorPort,
        state_store: DashboardStateStorePort,
        clock: Callable[[], str],
    ) -> None:
        self._workspace_driver = workspace_driver
        self._source_discovery = source_discovery
        self._excel_candidate_locator = excel_candidate_locator
        self._article_candidate_locator = article_candidate_locator
        self._orchestrator = orchestrator
        self._state_store = state_store
        self._clock = clock
        self._snapshots: dict[str, DashboardSnapshot] = {}

    def start_run(self, request: StartRunRequest) -> DashboardSnapshot:
        self._validate_request(request)
        workspace = self._call_without_snapshot(
            stage="workspace",
            code="WORKSPACE_OPERATION_FAILED",
            message="The workspace could not be created or restored.",
            operation=lambda: self._workspace_driver.create_or_restore(request),
        )

        snapshot = DashboardSnapshot.empty(
            run_id=workspace.run_id,
            journal_number=workspace.journal_number,
            source_folder=workspace.source_folder,
            output_folder=workspace.output_folder,
            timestamp=self._clock(),
        )
        snapshot = self._with_core(
            snapshot,
            CoreProjection(
                core_id="workspace_driver",
                state=CoreState.COMPLETED,
                completed_work=1,
                total_work=1,
                message="Workspace ready",
            ),
        )
        self._persist(snapshot)

        snapshot = self._with_core(
            snapshot.evolve(
                state=RunState.DISCOVERING,
                stage="source_discovery",
                updated_at=self._clock(),
            ),
            CoreProjection(
                core_id="source_discovery",
                state=CoreState.RUNNING,
                completed_work=0,
                total_work=1,
                message="Recursive discovery requested",
            ),
        )
        self._persist(snapshot)
        discovery = self._call_with_snapshot(
            snapshot=snapshot,
            stage="source_discovery",
            code="SOURCE_DISCOVERY_FAILED",
            message="Recursive source discovery could not finish.",
            operation=lambda: self._source_discovery.discover(
                workspace,
                recursive=True,
            ),
        )
        snapshot = self._with_core(
            snapshot.evolve(
                discovered_file_count=len(discovery.files),
                warnings=_merge_records(snapshot.warnings, discovery.warnings),
                updated_at=self._clock(),
            ),
            CoreProjection(
                core_id="source_discovery",
                state=(
                    CoreState.WARNING if discovery.warnings else CoreState.COMPLETED
                ),
                completed_work=1,
                total_work=1,
                message="Recursive discovery complete",
            ),
        )
        self._persist(snapshot)

        snapshot = snapshot.evolve(
            state=RunState.LOCATING_CANDIDATES,
            stage="candidate_location",
            updated_at=self._clock(),
        )
        snapshot = self._with_core(
            snapshot,
            CoreProjection(
                core_id="excel_candidate_locator",
                state=CoreState.RUNNING,
                completed_work=0,
                total_work=1,
                message="Locating Excel candidates",
            ),
        )
        snapshot = self._with_core(
            snapshot,
            CoreProjection(
                core_id="article_candidate_locator",
                state=CoreState.RUNNING,
                completed_work=0,
                total_work=1,
                message="Locating article candidates",
            ),
        )
        self._persist(snapshot)

        excel_candidates = self._locate_candidates(
            snapshot=snapshot,
            discovery=discovery,
            locator=self._excel_candidate_locator,
            code="EXCEL_CANDIDATE_LOCATION_FAILED",
            stage="excel_candidate_location",
            message="Excel candidates could not be located.",
        )
        snapshot = self._with_core(
            snapshot.evolve(
                excel_candidate_count=len(excel_candidates.candidates),
                warnings=_merge_records(
                    snapshot.warnings,
                    excel_candidates.warnings,
                ),
                stage="excel_candidate_location",
                updated_at=self._clock(),
            ),
            CoreProjection(
                core_id="excel_candidate_locator",
                state=(
                    CoreState.WARNING
                    if excel_candidates.warnings
                    else CoreState.COMPLETED
                ),
                completed_work=1,
                total_work=1,
                message="Excel candidate location complete",
            ),
        )
        self._persist(snapshot)

        article_candidates = self._locate_candidates(
            snapshot=snapshot,
            discovery=discovery,
            locator=self._article_candidate_locator,
            code="ARTICLE_CANDIDATE_LOCATION_FAILED",
            stage="article_candidate_location",
            message="Article candidates could not be located.",
        )
        snapshot = self._with_core(
            snapshot.evolve(
                article_candidate_count=len(article_candidates.candidates),
                warnings=_merge_records(
                    snapshot.warnings,
                    article_candidates.warnings,
                ),
                stage="article_candidate_location",
                updated_at=self._clock(),
            ),
            CoreProjection(
                core_id="article_candidate_locator",
                state=(
                    CoreState.WARNING
                    if article_candidates.warnings
                    else CoreState.COMPLETED
                ),
                completed_work=1,
                total_work=1,
                message="Article candidate location complete",
            ),
        )
        self._persist(snapshot)

        submission = WorkflowSubmission(
            workspace=workspace,
            discovery=discovery,
            excel_candidates=excel_candidates,
            article_candidates=article_candidates,
        )
        snapshot = self._with_core(
            snapshot.evolve(
                state=RunState.SUBMITTING,
                stage="orchestrator_submission",
                updated_at=self._clock(),
            ),
            CoreProjection(
                core_id="orchestrator_core",
                state=CoreState.RUNNING,
                completed_work=0,
                total_work=2,
                message="Workflow submitted",
            ),
        )
        self._persist(snapshot)
        try:
            result = self._orchestrator.submit(
                submission,
                lambda event: self._apply_event(workspace.run_id, event),
            )
        except DashboardOperationError:
            raise
        except Exception as error:
            current = self._snapshots.get(workspace.run_id, snapshot)
            self._raise_stage_failure(
                snapshot=current,
                stage="orchestrator_submission",
                code="ORCHESTRATOR_SUBMISSION_FAILED",
                message="The workflow could not be submitted to Orchestrator Core.",
                error=error,
            )

        return self._finish_orchestration(workspace.run_id, result)

    def get_run(self, run_id: str) -> DashboardSnapshot:
        if not isinstance(run_id, str) or not run_id.strip():
            self._raise_without_snapshot(
                code="RUN_NOT_FOUND",
                message="The requested dashboard run was not found.",
                stage="recovery",
                retryable=False,
            )
        if run_id in self._snapshots:
            return self._snapshots[run_id]
        try:
            snapshot = self._state_store.load(run_id)
        except Exception as error:
            code = (
                "DASHBOARD_STATE_INVALID"
                if isinstance(error, DashboardPortError)
                and error.code == "DASHBOARD_STATE_INVALID"
                else "DASHBOARD_STATE_PERSISTENCE_FAILED"
            )
            self._raise_without_snapshot(
                code=code,
                message="The dashboard state could not be loaded.",
                stage="recovery",
                retryable=_is_retryable(error),
                error=error,
            )
        if snapshot is None:
            self._raise_without_snapshot(
                code="RUN_NOT_FOUND",
                message="The requested dashboard run was not found.",
                stage="recovery",
                retryable=False,
            )
        self._snapshots[run_id] = snapshot
        return snapshot

    def resume_run(self, run_id: str) -> DashboardSnapshot:
        snapshot = self.get_run(run_id)
        if snapshot.state in {
            RunState.SUCCEEDED,
            RunState.SUCCEEDED_WITH_WARNINGS,
        }:
            return snapshot
        self._call_with_snapshot(
            snapshot=snapshot,
            stage="workspace_restore",
            code="WORKSPACE_OPERATION_FAILED",
            message="The workspace could not be restored.",
            operation=lambda: self._workspace_driver.restore(run_id),
        )
        snapshot = snapshot.evolve(
            state=RunState.RUNNING,
            stage="orchestrator_resume",
            final_result=None,
            failure=None,
            updated_at=self._clock(),
        )
        self._persist(snapshot)
        try:
            result = self._orchestrator.resume(
                run_id,
                lambda event: self._apply_event(run_id, event),
            )
        except DashboardOperationError:
            raise
        except Exception as error:
            current = self._snapshots.get(run_id, snapshot)
            self._raise_stage_failure(
                snapshot=current,
                stage="orchestrator_resume",
                code="ORCHESTRATOR_SUBMISSION_FAILED",
                message="Orchestrator Core could not resume the workflow.",
                error=error,
            )
        return self._finish_orchestration(run_id, result)

    def _validate_request(self, request: StartRunRequest) -> None:
        invalid = [
            name
            for name, value in (
                ("source_folder", request.source_folder),
                ("output_folder", request.output_folder),
                ("journal_number", request.journal_number),
            )
            if not isinstance(value, str) or not value.strip()
        ]
        if invalid:
            self._raise_without_snapshot(
                code="INVALID_DASHBOARD_REQUEST",
                message="Source folder, output folder, and journal number are required.",
                stage="request",
                retryable=False,
                details={"invalid_fields": invalid},
            )

    def _locate_candidates(
        self,
        *,
        snapshot: DashboardSnapshot,
        discovery: DiscoveryResult,
        locator: Any,
        code: str,
        stage: str,
        message: str,
    ) -> CandidateSet:
        return self._call_with_snapshot(
            snapshot=snapshot,
            stage=stage,
            code=code,
            message=message,
            operation=lambda: locator.locate(discovery),
        )

    def _apply_event(self, run_id: str, event: CoreEvent) -> None:
        snapshot = self._snapshots[run_id]
        if event.sequence <= snapshot.last_event_sequence:
            return
        snapshot = self._with_core(
            snapshot.evolve(
                state=RunState.RUNNING,
                stage=f"orchestrator:{event.core_id}",
                last_event_sequence=event.sequence,
                warnings=_merge_records(snapshot.warnings, event.warnings),
                reports=_merge_records(snapshot.reports, event.reports),
                files=_merge_records(snapshot.files, event.files),
                final_result=event.final_result or snapshot.final_result,
                updated_at=self._clock(),
            ),
            CoreProjection(
                core_id=event.core_id,
                state=event.state,
                completed_work=event.completed_work,
                total_work=event.total_work,
                message=event.message,
            ),
        )
        self._persist(snapshot)

    def _finish_orchestration(
        self,
        run_id: str,
        result: OrchestrationResult,
    ) -> DashboardSnapshot:
        snapshot = self._snapshots[run_id]
        final_result = result.final_result
        normalized_status = final_result.status.strip().upper()
        if normalized_status == "PASS" and not snapshot.warnings:
            state = RunState.SUCCEEDED
            failure = None
        elif normalized_status in {"PASS", "PASS WITH WARNINGS"}:
            state = RunState.SUCCEEDED_WITH_WARNINGS
            failure = None
        else:
            state = RunState.FAILED
            failure = DashboardFailure(
                code="WORKFLOW_FAILED",
                message="The workflow completed with a failed final result.",
                stage="orchestrator_result",
                retryable=False,
                details={"result_status": final_result.status},
            )
        snapshot = snapshot.evolve(
            state=state,
            stage="complete",
            final_result=final_result,
            failure=failure,
            updated_at=self._clock(),
        )
        self._persist(snapshot)
        return snapshot

    def _with_core(
        self,
        snapshot: DashboardSnapshot,
        projection: CoreProjection,
    ) -> DashboardSnapshot:
        cores = [item for item in snapshot.cores if item.core_id != projection.core_id]
        cores.append(projection)
        cores.sort(key=lambda item: item.core_id)
        completed = sum(item.completed_work for item in cores)
        total = sum(item.total_work for item in cores)
        return snapshot.evolve(
            cores=tuple(cores),
            completed_work=completed,
            total_work=total,
        )

    def _persist(self, snapshot: DashboardSnapshot) -> None:
        self._snapshots[snapshot.run_id] = snapshot
        try:
            self._state_store.save(snapshot)
        except DashboardOperationError:
            raise
        except Exception as error:
            failure = _failure_from_error(
                code="DASHBOARD_STATE_PERSISTENCE_FAILED",
                message="The dashboard state could not be persisted.",
                stage="persistence",
                error=error,
            )
            raise DashboardOperationError(
                failure=failure,
                snapshot=snapshot,
            ) from None

    def _call_without_snapshot(
        self,
        *,
        stage: str,
        code: str,
        message: str,
        operation: Callable[[], Any],
    ) -> Any:
        try:
            return operation()
        except DashboardOperationError:
            raise
        except Exception as error:
            self._raise_without_snapshot(
                code=code,
                message=message,
                stage=stage,
                retryable=_is_retryable(error),
                error=error,
            )

    def _call_with_snapshot(
        self,
        *,
        snapshot: DashboardSnapshot,
        stage: str,
        code: str,
        message: str,
        operation: Callable[[], Any],
    ) -> Any:
        try:
            return operation()
        except DashboardOperationError:
            raise
        except Exception as error:
            self._raise_stage_failure(
                snapshot=snapshot,
                stage=stage,
                code=code,
                message=message,
                error=error,
            )

    def _raise_stage_failure(
        self,
        *,
        snapshot: DashboardSnapshot,
        stage: str,
        code: str,
        message: str,
        error: Exception,
    ) -> None:
        failure = _failure_from_error(
            code=code,
            message=message,
            stage=stage,
            error=error,
        )
        failed = snapshot.evolve(
            state=RunState.FAILED,
            stage=stage,
            failure=failure,
            final_result=None,
            updated_at=self._clock(),
        )
        self._persist(failed)
        raise DashboardOperationError(failure=failure, snapshot=failed) from None

    def _raise_without_snapshot(
        self,
        *,
        code: str,
        message: str,
        stage: str,
        retryable: bool,
        error: Exception | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        safe_details = dict(details or {})
        if isinstance(error, DashboardPortError):
            safe_details["port_code"] = error.code
        failure = DashboardFailure(
            code=code,
            message=message,
            stage=stage,
            retryable=retryable,
            details=safe_details,
        )
        raise DashboardOperationError(failure=failure) from None


def _failure_from_error(
    *,
    code: str,
    message: str,
    stage: str,
    error: Exception,
) -> DashboardFailure:
    details: dict[str, Any] = {}
    if isinstance(error, DashboardPortError):
        details["port_code"] = error.code
    return DashboardFailure(
        code=code,
        message=message,
        stage=stage,
        retryable=_is_retryable(error),
        details=details,
    )


def _is_retryable(error: Exception) -> bool:
    return isinstance(error, DashboardPortError) and error.retryable


def _merge_records(
    existing: Iterable[RecordT],
    additions: Iterable[RecordT],
) -> tuple[RecordT, ...]:
    merged: list[RecordT] = []
    seen: set[str] = set()
    for record in (*tuple(existing), *tuple(additions)):
        if record.record_id in seen:
            continue
        seen.add(record.record_id)
        merged.append(record)
    return tuple(merged)
