from pathlib import Path

from journal_factory.word_render import render_docx_to_pdf


def test_word_render_blocks_when_input_is_missing(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "render_report.json"

    report = render_docx_to_pdf(
        tmp_path / "missing.docx",
        tmp_path / "missing.pdf",
        report_path,
    )

    assert report["status"] == "BLOCKED"
    assert report["blockers"] == ["input_docx_missing"]
    assert report_path.is_file()
