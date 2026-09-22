from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from astra_journal.fixture_factory import create_golden_fixture

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def test_golden_fixture_has_two_independent_reference_numids(tmp_path: Path) -> None:
    path = create_golden_fixture(tmp_path / "golden.docx")
    with ZipFile(path) as zf:
        document = etree.fromstring(zf.read("word/document.xml"))
        numbering = etree.fromstring(zf.read("word/numbering.xml"))

    num_ids = [
        node.get(f"{{{W}}}val")
        for node in document.findall(".//w:numPr/w:numId", NS)
    ]
    assert "101" in num_ids
    assert "102" in num_ids

    starts = {}
    for num in numbering.findall("w:num", NS):
        num_id = num.get(f"{{{W}}}numId")
        override = num.find("w:lvlOverride/w:startOverride", NS)
        if num_id in {"101", "102"}:
            starts[num_id] = override.get(f"{{{W}}}val")
    assert starts == {"101": "1", "102": "1"}


def test_golden_fixture_contains_front_matter_and_media(tmp_path: Path) -> None:
    path = create_golden_fixture(tmp_path / "golden.docx")
    with ZipFile(path) as zf:
        text = zf.read("word/document.xml").decode("utf-8")
        media = [name for name in zf.namelist() if name.startswith("word/media/")]
    assert "FRONT MATTER SENTINEL" in text
    assert media
