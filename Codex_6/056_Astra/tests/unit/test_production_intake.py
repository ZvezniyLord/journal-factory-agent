from pathlib import Path
import zipfile

import pytest

from astra_journal.production_intake import (
    IntakeBlocked,
    detect_conference_number,
    extract_and_inventory,
)


def test_detect_conference_number() -> None:
    assert detect_conference_number("153_м_Харків_3-5_вересня.rar") == "153"


def test_ambiguous_numbers_block() -> None:
    with pytest.raises(IntakeBlocked):
        detect_conference_number("153_154.rar")


def test_zip_inventory(tmp_path: Path) -> None:
    archive = tmp_path / "153_test.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("153 participants.xlsx", b"x")
        zf.writestr("Article One.docx", b"x")
    result = extract_and_inventory(archive, tmp_path / "run")
    assert result.conference_number == "153"
    assert result.registry_candidates
    assert result.article_candidates
