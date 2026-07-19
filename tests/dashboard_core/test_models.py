from __future__ import annotations

import unittest

from journal_factory.dashboard_core.models import (
    CoreEvent,
    CoreProjection,
    CoreState,
    DashboardFailure,
    DashboardSnapshot,
    FileRecord,
    FinalResult,
    ReportRecord,
    RunState,
    WarningRecord,
)


class DashboardSnapshotTests(unittest.TestCase):
    def test_snapshot_round_trips_without_losing_typed_records(self) -> None:
        snapshot = DashboardSnapshot(
            schema_version=1,
            revision=7,
            run_id="run-001",
            journal_number="137",
            state=RunState.SUCCEEDED_WITH_WARNINGS,
            stage="complete",
            source_folder="C:/sample/source",
            output_folder="C:/sample/output",
            created_at="2026-07-19T20:00:00Z",
            updated_at="2026-07-19T20:01:00Z",
            last_event_sequence=4,
            completed_work=3,
            total_work=3,
            discovered_file_count=4,
            excel_candidate_count=1,
            article_candidate_count=2,
            cores=(
                CoreProjection(
                    core_id="source_discovery",
                    state=CoreState.COMPLETED,
                    completed_work=1,
                    total_work=1,
                    message="Recursive scan complete",
                ),
            ),
            warnings=(
                WarningRecord(
                    record_id="warning-1",
                    code="UNSUPPORTED_FILE",
                    message="One asset was not classified",
                    producer_core="source_discovery",
                ),
            ),
            reports=(
                ReportRecord(
                    record_id="report-1",
                    producer_core="source_discovery",
                    kind="source_inventory",
                    display_name="Source inventory",
                    reference="reports/source_inventory.json",
                    status="complete",
                    digest="sha256:abc",
                ),
            ),
            files=(
                FileRecord(
                    record_id="file-1",
                    producer_core="orchestrator_core",
                    kind="result",
                    display_name="Run result",
                    reference="final/result.json",
                    status="ready",
                    digest=None,
                ),
            ),
            final_result=FinalResult(
                status="PASS WITH WARNINGS",
                production_ready=False,
                message="Operator review required",
            ),
            failure=None,
        )

        restored = DashboardSnapshot.from_dict(snapshot.to_dict())

        self.assertEqual(restored, snapshot)
        self.assertEqual(restored.progress_percent, 100.0)
        self.assertFalse(restored.final_result.production_ready)

    def test_success_state_requires_an_explicit_final_result(self) -> None:
        with self.assertRaisesRegex(ValueError, "final result"):
            DashboardSnapshot.empty(
                run_id="run-001",
                journal_number="137",
                source_folder="source",
                output_folder="output",
                timestamp="2026-07-19T20:00:00Z",
            ).evolve(state=RunState.SUCCEEDED, stage="complete")

    def test_failed_state_requires_a_structured_failure(self) -> None:
        with self.assertRaisesRegex(ValueError, "failure"):
            DashboardSnapshot.empty(
                run_id="run-001",
                journal_number="137",
                source_folder="source",
                output_folder="output",
                timestamp="2026-07-19T20:00:00Z",
            ).evolve(state=RunState.FAILED, stage="discovery")

    def test_failure_round_trip_preserves_json_safe_details(self) -> None:
        failure = DashboardFailure(
            code="SOURCE_DISCOVERY_FAILED",
            message="Source discovery could not finish",
            stage="discovery",
            retryable=True,
            details={"attempt": 1},
        )

        self.assertEqual(
            DashboardFailure.from_dict(failure.to_dict()),
            failure,
        )

    def test_persisted_booleans_are_not_coerced_from_strings(self) -> None:
        with self.assertRaisesRegex(ValueError, "boolean"):
            FinalResult.from_dict(
                {
                    "status": "PASS",
                    "production_ready": "false",
                    "message": "Not a valid typed payload",
                }
            )
        with self.assertRaisesRegex(ValueError, "boolean"):
            DashboardFailure.from_dict(
                {
                    "code": "TEST",
                    "message": "Not a valid typed payload",
                    "stage": "test",
                    "retryable": "true",
                    "details": {},
                }
            )


class CoreEventTests(unittest.TestCase):
    def test_rejects_negative_progress(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-negative"):
            CoreEvent(
                sequence=1,
                core_id="source_discovery",
                state=CoreState.RUNNING,
                completed_work=-1,
                total_work=2,
            )

    def test_rejects_completed_work_greater_than_total(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            CoreEvent(
                sequence=1,
                core_id="source_discovery",
                state=CoreState.RUNNING,
                completed_work=3,
                total_work=2,
            )

    def test_zero_total_progress_is_zero(self) -> None:
        event = CoreEvent(
            sequence=1,
            core_id="source_discovery",
            state=CoreState.RUNNING,
            completed_work=0,
            total_work=0,
        )

        self.assertEqual(event.progress_percent, 0.0)


if __name__ == "__main__":
    unittest.main()
