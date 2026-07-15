from pathlib import Path
from zipfile import ZipFile

import pytest

from journal_factory.archive_workspace import prepare_archive_workspace, sha256_file


def test_safe_zip_extraction(tmp_path: Path) -> None:
    archive = tmp_path / "safe.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("articles/a.txt", "alpha")

    report = prepare_archive_workspace(archive, tmp_path / "workspace", tmp_path / "reports")

    assert report["source_type"] == "zip"
    assert (tmp_path / "workspace" / "source" / "articles" / "a.txt").exists()


def test_zip_slip_blocked(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("../evil.txt", "bad")

    with pytest.raises(ValueError):
        prepare_archive_workspace(archive, tmp_path / "workspace", tmp_path / "reports")


def test_directory_input_and_stable_hashes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    file_path = source / "article.docx"
    file_path.write_bytes(b"same")

    first = prepare_archive_workspace(source, tmp_path / "workspace", tmp_path / "reports")
    second = prepare_archive_workspace(source, tmp_path / "workspace", tmp_path / "reports")

    assert first["source_type"] == "directory"
    assert first["files"][0]["sha256"] == second["files"][0]["sha256"] == sha256_file(file_path)


def test_office_temp_files_ignored(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "~$temp.docx").write_bytes(b"temp")
    (source / "article.docx").write_bytes(b"article")

    report = prepare_archive_workspace(source, tmp_path / "workspace", tmp_path / "reports")
    by_path = {item["path"]: item for item in report["files"]}

    assert by_path["~$temp.docx"]["article_candidate"] is False
    assert by_path["article.docx"]["article_candidate"] is True
