import zipfile
from pathlib import Path

import pytest

from journal_factory.corpus_archive import (
    ArchiveValidationError,
    detect_archive,
    extract_archive_readonly,
    list_archive_entries,
    validate_entries,
)


def test_safe_zip_round_trip(tmp_path: Path):
    archive = tmp_path / "95.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("article.docx", b"PK-fake")
        stream.writestr("nested/note.txt", "hello")
    assert detect_archive(archive) == "ZIP"
    entries = list_archive_entries(archive, "ZIP")
    assert validate_entries(entries, archive.stat().st_size)["entry_count"] == 2
    destination = tmp_path / "out"
    extract_archive_readonly(archive, destination, "ZIP")
    assert (destination / "nested" / "note.txt").read_text() == "hello"


def test_zip_path_traversal_is_blocked(tmp_path: Path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("../escape.txt", "bad")
    with pytest.raises(ArchiveValidationError, match="PATH_TRAVERSAL"):
        validate_entries(list_archive_entries(archive, "ZIP"), archive.stat().st_size)
