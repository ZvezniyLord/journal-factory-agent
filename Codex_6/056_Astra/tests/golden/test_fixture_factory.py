from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from astra_journal.fixture_factory import create_golden_fixture

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def test_golden_fixture_uses_shared_abstract_and_per_article_numids(tmp_path: Path) -> None:
    path = create_golden_fixture(tmp_path / "golden.docx")
    with ZipFile(path) as zf:
        document = etree.fromstring(zf.read("word/document.xml"))
        numbering = etree.fromstring(zf.read("word/numbering.xml"))

    num_ids = [
        node.get(f"{{{W}}}val")
        for node in document.findall(".//w:numPr/w:numId", NS)
    ]
    distinct_used = []
    for value in num_ids:
        if value not in distinct_used:
            distinct_used.append(value)

    assert len(distinct_used) == 2

    abstract_refs = {}
    overrides = {}
    for num in numbering.findall("w:num", NS):
        num_id = num.get(f"{{{W}}}numId")
        if num_id not in set(distinct_used):
            continue
        abstract = num.find("w:abstractNumId", NS)
        override = num.find("w:lvlOverride/w:startOverride", NS)
        abstract_refs[num_id] = abstract.get(f"{{{W}}}val")
        overrides[num_id] = (
            override.get(f"{{{W}}}val") if override is not None else None
        )

    assert len(set(abstract_refs.values())) == 1
    assert overrides[distinct_used[0]] is None
    assert overrides[distinct_used[1]] == "1"


def test_golden_fixture_contains_front_matter_and_media(tmp_path: Path) -> None:
    path = create_golden_fixture(tmp_path / "golden.docx")
    with ZipFile(path) as zf:
        text = zf.read("word/document.xml").decode("utf-8")
        media = [name for name in zf.namelist() if name.startswith("word/media/")]
    assert "FRONT MATTER SENTINEL" in text
    assert media
