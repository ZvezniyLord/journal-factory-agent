from __future__ import annotations

import base64
import io
from pathlib import Path
import zipfile

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE

from journal_factory.document_composer import compose_articles_into_etalon, find_article_insert_index


ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZlFsAAAAASUVORK5CYII="
)


def test_article_is_inserted_after_toc_and_before_tail_with_objects(tmp_path: Path) -> None:
    master_path = tmp_path / "etalon.docx"
    article_path = tmp_path / "article.docx"
    output_path = tmp_path / "journal.docx"

    master = Document()
    master.styles.add_style("SECTION", WD_STYLE_TYPE.PARAGRAPH)
    master.add_paragraph("FRONT MATTER")
    master.add_paragraph("TABLE OF CONTENTS")
    master.add_section(WD_SECTION.NEW_PAGE)
    master.add_paragraph("FINAL SERVICE PAGE")
    master.save(master_path)

    assert find_article_insert_index(Document(master_path)) > 0

    article = Document()
    article.add_paragraph("UNIQUE ARTICLE BODY")
    article.add_table(rows=1, cols=1).cell(0, 0).text = "TABLE CELL"
    article.add_picture(io.BytesIO(ONE_PIXEL_PNG))
    article.save(article_path)

    report = compose_articles_into_etalon(
        master_path,
        [
            {
                "article_id": "article-001",
                "source_file": str(article_path),
                "section": "SECTION ONE",
            }
        ],
        output_path,
    )

    assert report["status"] == "PASS"
    assert report["inserted_count"] == 1
    output = Document(output_path)
    texts = [paragraph.text for paragraph in output.paragraphs]
    assert texts.index("TABLE OF CONTENTS") < texts.index("UNIQUE ARTICLE BODY")
    assert texts.index("UNIQUE ARTICLE BODY") < texts.index("FINAL SERVICE PAGE")
    assert len(output.tables) == 1
    assert output.tables[0].cell(0, 0).text == "TABLE CELL"

    with zipfile.ZipFile(output_path) as package:
        media = [name for name in package.namelist() if name.startswith("word/media/")]
    assert media


def test_missing_toc_anchor_fails_closed(tmp_path: Path) -> None:
    master_path = tmp_path / "bad-etalon.docx"
    master = Document()
    master.add_paragraph("NO TOC")
    master.save(master_path)

    try:
        find_article_insert_index(Document(master_path))
    except ValueError as exc:
        assert "TABLE OF CONTENTS" in str(exc)
    else:
        raise AssertionError("Missing TOC anchor must fail closed")
