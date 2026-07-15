from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import shutil

from journal_factory.source_snapshot import create_source_snapshot, snapshot_docx, snapshot_legacy_doc


FIXTURE_DOCX = Path("fixtures/manifest/articles/article_alpha.docx")


def test_paragraphs_and_runs_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    docx = source / "article.docx"
    shutil.copy2(FIXTURE_DOCX, docx)

    snapshot = create_source_snapshot(docx, "article-001", tmp_path / "snapshots", source)

    assert snapshot["snapshot_status"] == "PASS"
    assert snapshot["paragraphs"]
    assert snapshot["runs"]
    assert "Alice Example" in snapshot["visible_text"]


def test_table_text_and_merge_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    docx = source / "article.docx"
    shutil.copy2(FIXTURE_DOCX, docx)

    snapshot = snapshot_docx(docx, source)

    assert any(cell["text"] == "Cell A1" for cell in snapshot["table_cells"])
    assert isinstance(snapshot["merge_map"], list)


def test_image_media_hash_and_textbox_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    docx = source / "article.docx"
    shutil.copy2(FIXTURE_DOCX, docx)

    snapshot = snapshot_docx(docx, source)

    assert snapshot["media_hashes"]
    assert any(box["text"] == "Textbox synthetic note" for box in snapshot["textboxes"])


def test_numbering_xml_snapshot(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    docx = source / "article.docx"
    shutil.copy2(FIXTURE_DOCX, docx)

    snapshot = snapshot_docx(docx, source)

    assert snapshot["numbering"]["present"] is True
    assert snapshot["numbering"]["sha256"]


def test_unsupported_ooxml_part_produces_blocker(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    docx = source / "article.docx"
    shutil.copy2(FIXTURE_DOCX, docx)
    tmp = source / "patched.docx"
    with ZipFile(docx, "r") as zin, ZipFile(tmp, "w", ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, zin.read(item.filename))
        zout.writestr("word/activeX/activeX1.xml", "<root/>")
    tmp.replace(docx)

    snapshot = snapshot_docx(docx, source)

    assert snapshot["snapshot_status"] == "BLOCKED"
    assert "unsupported_ooxml_parts" in snapshot["blockers"]


def test_legacy_doc_conversion_failure_blocks(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    doc = source / "legacy.doc"
    doc.write_bytes(b"legacy binary placeholder")

    snapshot = snapshot_legacy_doc(doc, source)

    assert snapshot["snapshot_status"] == "BLOCKED"
    assert snapshot["object_risk"] == "unverified"
    assert "legacy_doc_conversion_not_available" in snapshot["blockers"]
