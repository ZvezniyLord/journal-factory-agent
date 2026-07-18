from pathlib import Path

from docx import Document

from journal_factory.article_preparation import prepare_article_source
from journal_factory.builder_fidelity import normalize_visible_text
from journal_factory.source_snapshot import extract_docx_evidence_text


def test_embedded_application_tail_is_removed_without_changing_article_prefix(tmp_path: Path) -> None:
    source = tmp_path / "combined.docx"
    document = Document()
    document.add_paragraph("AUTHOR")
    document.add_paragraph("ARTICLE TITLE")
    document.add_paragraph("IMMUTABLE ARTICLE BODY")
    document.add_paragraph("АНКЕТА УЧАСНИКА МІЖНАРОДНОЇ КОНФЕРЕНЦІЇ")
    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "PRIVATE APPLICATION DATA"
    document.save(source)

    prepared, report = prepare_article_source(
        source,
        {
            "article_id": "article-001",
            "source_path": "submissions/1 Author/combined.docx",
            "provenance": {"embedded_service_tail": True},
        },
        tmp_path / "prepared",
    )

    text = normalize_visible_text(extract_docx_evidence_text(prepared))
    assert report["status"] == "PASS"
    assert report["transformation"] == "remove_embedded_application_tail"
    assert report["preserved_article_text"] is True
    assert text == "AUTHOR ARTICLE TITLE IMMUTABLE ARTICLE BODY"
    assert "PRIVATE APPLICATION DATA" not in text


def test_article_without_service_tail_is_not_rewritten(tmp_path: Path) -> None:
    source = tmp_path / "article.docx"
    document = Document()
    document.add_paragraph("ARTICLE BODY")
    document.save(source)

    prepared, report = prepare_article_source(
        source,
        {
            "article_id": "article-001",
            "source_path": "article.docx",
            "provenance": {"embedded_service_tail": False},
        },
        tmp_path / "prepared",
    )

    assert prepared == source
    assert report["transformation"] == "none"
    assert report["source_sha256"] == report["prepared_sha256"]
