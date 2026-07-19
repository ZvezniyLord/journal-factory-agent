from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from journal_factory.dashboard_core.models import DashboardSnapshot
from journal_factory.dashboard_core.persistence import JsonDashboardStateStore
from journal_factory.dashboard_core.ports import DashboardPortError


class JsonDashboardStateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.store = JsonDashboardStateStore(self.root)
        self.snapshot = DashboardSnapshot.empty(
            run_id="run-137",
            journal_number="137",
            source_folder="C:/source/Матеріали",
            output_folder="C:/output",
            timestamp="2026-07-19T20:00:00Z",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_save_is_utf8_json_and_load_round_trips(self) -> None:
        self.store.save(self.snapshot)

        state_path = self.store.state_path(self.snapshot.run_id)
        parsed = json.loads(state_path.read_text(encoding="utf-8"))
        restored = JsonDashboardStateStore(self.root).load(self.snapshot.run_id)

        self.assertEqual(parsed["source_folder"], self.snapshot.source_folder)
        self.assertEqual(restored, self.snapshot)
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_missing_run_returns_none(self) -> None:
        self.assertIsNone(self.store.load("missing-run"))

    def test_corrupt_json_is_a_typed_invalid_state_failure(self) -> None:
        self.store.state_path("run-137").write_text("{broken", encoding="utf-8")

        with self.assertRaises(DashboardPortError) as raised:
            self.store.load("run-137")

        self.assertEqual(raised.exception.code, "DASHBOARD_STATE_INVALID")
        self.assertFalse(raised.exception.retryable)

    def test_payload_run_id_must_match_requested_run(self) -> None:
        self.store.save(self.snapshot)
        state_path = self.store.state_path(self.snapshot.run_id)
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        payload["run_id"] = "different-run"
        state_path.write_text(json.dumps(payload), encoding="utf-8")

        with self.assertRaises(DashboardPortError) as raised:
            self.store.load(self.snapshot.run_id)

        self.assertEqual(raised.exception.code, "DASHBOARD_STATE_INVALID")

    def test_failed_atomic_replace_preserves_last_good_snapshot(self) -> None:
        self.store.save(self.snapshot)
        changed = self.snapshot.evolve(
            stage="changed",
            updated_at="2026-07-19T20:01:00Z",
        )

        def fail_replace(source: Path, destination: Path) -> None:
            raise OSError("deterministic replace failure")

        failing_store = JsonDashboardStateStore(
            self.root,
            replace_file=fail_replace,
        )
        with self.assertRaises(DashboardPortError) as raised:
            failing_store.save(changed)

        self.assertEqual(
            raised.exception.code,
            "DASHBOARD_STATE_PERSISTENCE_FAILED",
        )
        self.assertTrue(raised.exception.retryable)
        self.assertEqual(self.store.load(self.snapshot.run_id), self.snapshot)
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_state_path_cannot_escape_the_supplied_directory(self) -> None:
        state_path = self.store.state_path("../../outside")

        self.assertEqual(state_path.parent, self.root.resolve())
        self.assertEqual(state_path.suffix, ".json")


if __name__ == "__main__":
    unittest.main()
