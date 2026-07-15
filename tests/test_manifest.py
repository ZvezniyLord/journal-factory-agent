from pathlib import Path
import json
import shutil

from journal_factory.archive_workspace import prepare_archive_workspace
from journal_factory.manifest import build_article_manifest


FIXTURE = Path("fixtures/manifest")


def _workspace_from_fixture(tmp_path: Path) -> Path:
    source = tmp_path / "fixture"
    shutil.copytree(FIXTURE, source)
    report = prepare_archive_workspace(source, tmp_path / "build" / "workspace", tmp_path / "build" / "reports")
    return Path(report["workspace_source"])


def _load_manifest(path: Path) -> dict:
    manifest = path / "applications" / "manifest.json"
    return json.loads(manifest.read_text(encoding="utf-8"))


def _write_manifest(path: Path, data: dict) -> None:
    (path / "applications" / "manifest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_article_matched_by_author_and_title(tmp_path: Path) -> None:
    workspace = _workspace_from_fixture(tmp_path)

    manifest = build_article_manifest(workspace, tmp_path / "build" / "reports")

    assert manifest["manifest_status"] == "PASS"
    assert [item["match_status"] for item in manifest["articles"]] == ["MATCHED", "MATCHED"]


def test_filename_only_match_rejected(tmp_path: Path) -> None:
    workspace = _workspace_from_fixture(tmp_path)
    data = _load_manifest(workspace)
    data["articles"][0]["authors_manifest"] = ["Nobody"]
    data["articles"][0]["title_manifest"] = "article_alpha"
    _write_manifest(workspace, data)

    manifest = build_article_manifest(workspace, tmp_path / "build" / "reports")

    assert manifest["articles"][0]["match_status"] == "BLOCKED"


def test_author_only_match_rejected(tmp_path: Path) -> None:
    workspace = _workspace_from_fixture(tmp_path)
    data = _load_manifest(workspace)
    data["articles"][0]["title_manifest"] = "Missing title"
    _write_manifest(workspace, data)

    manifest = build_article_manifest(workspace, tmp_path / "build" / "reports")

    assert "title_evidence_missing" in manifest["articles"][0]["blockers"]


def test_title_only_match_rejected(tmp_path: Path) -> None:
    workspace = _workspace_from_fixture(tmp_path)
    data = _load_manifest(workspace)
    data["articles"][0]["authors_manifest"] = ["Missing Author"]
    _write_manifest(workspace, data)

    manifest = build_article_manifest(workspace, tmp_path / "build" / "reports")

    assert "author_evidence_missing" in manifest["articles"][0]["blockers"]


def test_duplicate_article_match_blocked(tmp_path: Path) -> None:
    workspace = _workspace_from_fixture(tmp_path)
    data = _load_manifest(workspace)
    duplicate = dict(data["articles"][0])
    duplicate["article_id"] = "synthetic-duplicate"
    duplicate["journal_order"] = 3
    data["articles"].append(duplicate)
    _write_manifest(workspace, data)

    manifest = build_article_manifest(workspace, tmp_path / "build" / "reports")

    duplicate_entries = [item for item in manifest["articles"] if item["source_path"] == "articles/article_alpha.docx"]
    assert all("source_article_matches_multiple_manifest_records" in item["blockers"] for item in duplicate_entries)


def test_duplicate_journal_order_blocked(tmp_path: Path) -> None:
    workspace = _workspace_from_fixture(tmp_path)
    data = _load_manifest(workspace)
    data["articles"][1]["journal_order"] = data["articles"][0]["journal_order"]
    _write_manifest(workspace, data)

    manifest = build_article_manifest(workspace, tmp_path / "build" / "reports")

    assert "duplicate_journal_order:1" in manifest["blockers"]


def test_free_listener_excluded_from_articles(tmp_path: Path) -> None:
    workspace = _workspace_from_fixture(tmp_path)

    manifest = build_article_manifest(workspace, tmp_path / "build" / "reports")

    assert manifest["article_count"] == 2
    assert manifest["free_listener_count"] == 1
    assert manifest["free_listeners"][0]["full_name"] == "Free Listener"
