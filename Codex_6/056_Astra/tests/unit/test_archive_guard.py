from pathlib import Path
from zipfile import ZipFile

import pytest

from astra_journal.archive_guard import UnsafeArchivePath, safe_extract_zip


def _make_zip(path: Path, members: dict[str, str]) -> None:
    with ZipFile(path, "w") as archive:
        for name, value in members.items():
            archive.writestr(name, value)


def test_safe_extract_zip_extracts_normal_members(tmp_path: Path) -> None:
    archive = tmp_path / "safe.zip"
    _make_zip(archive, {"a/b.txt": "ok"})
    target = tmp_path / "out"
    extracted = safe_extract_zip(archive, target)
    assert (target / "a" / "b.txt").read_text() == "ok"
    assert len(extracted) == 1


def test_safe_extract_zip_rejects_parent_escape(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    _make_zip(archive, {"../outside.txt": "bad"})
    with pytest.raises(UnsafeArchivePath):
        safe_extract_zip(archive, tmp_path / "out")
