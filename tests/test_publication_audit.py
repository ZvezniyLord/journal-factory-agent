from pathlib import Path

import fitz

from journal_factory.publication_audit import (
    audit_pdf_pages,
    expected_first_article_pages,
)


def _write_numbered_pdf(path: Path, footer_numbers: list[int | None]) -> None:
    document = fitz.open()
    for index, footer_number in enumerate(footer_numbers, start=1):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 100), f"Publication content for page {index}", fontsize=14)
        if footer_number is not None:
            page.insert_text((295, 820), str(footer_number), fontsize=10)
    document.save(path)
    document.close()


def test_pdf_page_audit_confirms_continuous_visible_pagination(tmp_path: Path) -> None:
    pdf = tmp_path / "numbered.pdf"
    _write_numbered_pdf(pdf, [None, 2, 3])

    report = audit_pdf_pages(pdf, expected_page_count=3)

    assert report["status"] == "PASS"
    assert report["all_pages_inspected"] is True
    assert report["footer_page_numbers_present"] == 2
    assert report["title_page_number_hidden"] is True
    assert report["blank_pages"] == []


def test_pdf_page_audit_blocks_missing_footer_number(tmp_path: Path) -> None:
    pdf = tmp_path / "broken.pdf"
    _write_numbered_pdf(pdf, [None, 2, None])

    report = audit_pdf_pages(pdf, expected_page_count=3)

    assert report["status"] == "BLOCKED"
    assert report["missing_footer_numbers"] == [3]


def test_expected_first_article_page_uses_official_printed_number() -> None:
    official_toc = {
        "page_numbering": {"physical_to_printed_offset": 2},
        "articles": [{"physical_start_page": 8, "printed_start_page": 6}],
    }

    assert expected_first_article_pages(8, official_toc) == (8, 6)
    assert expected_first_article_pages(8) == (8, 8)
