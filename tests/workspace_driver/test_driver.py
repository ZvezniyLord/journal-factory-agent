from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from journal_factory.workspace_driver.adapters import LocalFileSystemAdapter
from journal_factory.workspace_driver.driver import WorkspaceDriver
from journal_factory.workspace_driver.errors import WorkspaceError
from journal_factory.workspace_driver.models import WorkspaceRequest


class FixedClock:
    def __init__(self) -> None:
        self._second = 0

    def now(self) -> datetime:
        value = datetime(2026, 7, 19, 21, 30, self._second, tzinfo=timezone.utc)
        self._second += 1
        return value


class FailingCreateAdapter(LocalFileSystemAdapter):
    def make_directory(self, path: Path) -> None:
        raise OSError("private filesystem detail")


class FailingValidationAdapter(LocalFileSystemAdapter):
    def exists(self, path: Path) -> bool:
        raise OSError("private validation detail")


class WorkspaceDriverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "conference.zip"
        self.source.write_bytes(b"immutable source")
        self.output = self.root / "output"
        self.output.mkdir()
        self.desktop = self.root / "Desktop"
        self.desktop.mkdir()
        self.state = self.root / "state"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_driver(self, filesystem=None, state_directory=None) -> WorkspaceDriver:
        return WorkspaceDriver(
            filesystem=filesystem or LocalFileSystemAdapter(),
            desktop_path=self.desktop,
            state_directory=state_directory or self.state,
            clock=FixedClock(),
        )

    def request(self, **changes: str) -> WorkspaceRequest:
        values = {
            "source_path": str(self.source),
            "output_parent": str(self.output),
            "journal_number": "95",
        }
        values.update(changes)
        return WorkspaceRequest(**values)

    def test_validate_normalizes_explicit_paths_without_creating_workspace(self) -> None:
        validation = self.make_driver().validate(self.request())

        self.assertTrue(validation.valid)
        self.assertEqual(self.source.resolve(), validation.config.source_path)
        self.assertEqual(self.output.resolve(), validation.config.output_parent)
        self.assertEqual((self.output / "95").resolve(), validation.workspace_path)
        self.assertFalse(validation.workspace_path.exists())

    def test_blank_output_uses_desktop_and_missing_journal_is_blocked(self) -> None:
        driver = self.make_driver()

        defaulted = driver.validate(self.request(output_parent=""))
        blocked = driver.validate(self.request(journal_number=""))

        self.assertEqual(self.desktop.resolve(), defaulted.config.output_parent)
        self.assertEqual((self.desktop / "95").resolve(), defaulted.workspace_path)
        self.assertFalse(blocked.valid)
        self.assertEqual("JOURNAL_NUMBER_REQUIRED", blocked.errors[0].code)

    def test_unsafe_journal_number_is_sanitized_deterministically(self) -> None:
        validation = self.make_driver().validate(
            self.request(journal_number=" 95 / 2026:* ")
        )

        self.assertTrue(validation.valid)
        self.assertEqual("95_2026", validation.config.journal_number)
        self.assertEqual("JOURNAL_NUMBER_SANITIZED", validation.warnings[0].code)
        self.assertEqual((self.output / "95_2026").resolve(), validation.workspace_path)

    def test_create_builds_canonical_tree_and_parseable_registered_reports(self) -> None:
        status = self.make_driver().create(self.request())

        expected_keys = {
            "workspace",
            "source_snapshot",
            "articles_raw",
            "articles_transformed",
            "reports",
            "logs",
            "database",
            "rendered_pdf",
            "rendered_png",
            "final",
            "temp",
        }
        self.assertEqual(expected_keys, set(status.paths))
        self.assertTrue(all(path.is_absolute() and path.is_dir() for path in status.paths.values()))

        expected_reports = {
            "run_manifest",
            "action_log",
            "path_registry",
            "report_registry",
            "run_summary",
            "dashboard_state",
        }
        self.assertEqual(expected_reports, set(status.reports))
        self.assertTrue(all(path.is_absolute() for path in status.reports.values()))
        self.assertTrue(all(path.exists() for path in status.reports.values() if path.name != "dashboard_state.json"))

        manifest = json.loads(status.reports["run_manifest"].read_text(encoding="utf-8"))
        paths = json.loads(status.reports["path_registry"].read_text(encoding="utf-8"))
        reports = json.loads(status.reports["report_registry"].read_text(encoding="utf-8"))
        actions = [
            json.loads(line)
            for line in status.reports["action_log"].read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(status.run_id, manifest["run_id"])
        self.assertEqual(str(self.source.resolve()), manifest["source_path"])
        self.assertEqual("95", manifest["journal_number"])
        self.assertEqual(expected_keys, set(paths["paths"]))
        self.assertEqual(expected_reports, set(reports["reports"]))
        self.assertGreaterEqual(len(actions), len(expected_keys) + 5)
        self.assertEqual(list(range(1, len(actions) + 1)), [item["sequence"] for item in actions])
        self.assertTrue(all(item["timestamp_utc"].endswith("Z") for item in actions))
        directory_actions = {
            item["inputs"]["path_key"]
            for item in actions
            if item["action"] == "directory_created"
        }
        registered_reports = {
            item["inputs"]["report"]
            for item in actions
            if item["action"] == "report_registered"
        }
        self.assertEqual(expected_keys, directory_actions)
        self.assertEqual(expected_reports, registered_reports)

    def test_repeat_create_restores_same_run_without_overwriting_user_file(self) -> None:
        driver = self.make_driver()
        first = driver.create(self.request())
        user_file = first.paths["workspace"] / "operator-note.txt"
        user_file.write_text("keep", encoding="utf-8")

        second = driver.create(self.request())

        self.assertEqual(first.run_id, second.run_id)
        self.assertTrue(second.restored)
        self.assertEqual("keep", user_file.read_text(encoding="utf-8"))

    def test_existing_unmanaged_workspace_uses_collision_safe_directory(self) -> None:
        unmanaged = self.output / "95"
        unmanaged.mkdir()
        (unmanaged / "foreign.txt").write_text("keep", encoding="utf-8")

        status = self.make_driver().create(self.request())

        self.assertNotEqual(unmanaged.resolve(), status.paths["workspace"])
        self.assertTrue(status.paths["workspace"].name.startswith("95_run-"))
        self.assertEqual("keep", (unmanaged / "foreign.txt").read_text(encoding="utf-8"))

    def test_status_is_reconstructed_from_persisted_run_index(self) -> None:
        first_driver = self.make_driver()
        created = first_driver.create(self.request())

        restored = self.make_driver().status(created.run_id)

        self.assertEqual(created.run_id, restored.run_id)
        self.assertEqual(created.paths, restored.paths)
        self.assertEqual(created.reports, restored.reports)
        self.assertTrue(restored.restored)

    def test_managed_workspace_is_restored_when_external_run_index_is_missing(self) -> None:
        first = self.make_driver(state_directory=self.root / "state-a").create(self.request())
        note = first.paths["workspace"] / "operator-note.txt"
        note.write_text("keep", encoding="utf-8")

        restored = self.make_driver(state_directory=self.root / "state-b").create(self.request())

        self.assertEqual(first.run_id, restored.run_id)
        self.assertTrue(restored.restored)
        self.assertEqual("keep", note.read_text(encoding="utf-8"))

    def test_filesystem_failure_is_typed_and_suppresses_private_detail(self) -> None:
        driver = self.make_driver(filesystem=FailingCreateAdapter())

        with self.assertRaises(WorkspaceError) as caught:
            driver.create(self.request())

        self.assertEqual("WORKSPACE_CREATE_FAILED", caught.exception.code)
        self.assertNotIn("private filesystem detail", caught.exception.message)

    def test_validation_filesystem_failure_is_typed_and_suppressed(self) -> None:
        driver = self.make_driver(filesystem=FailingValidationAdapter())

        with self.assertRaises(WorkspaceError) as caught:
            driver.validate(self.request())

        self.assertEqual("FILESYSTEM_ACCESS_FAILED", caught.exception.code)
        self.assertEqual(503, caught.exception.status)
        self.assertNotIn("private validation detail", caught.exception.message)


if __name__ == "__main__":
    unittest.main()
