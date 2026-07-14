from journal_factory.ingest import is_article_candidate


def test_article_candidate_rejects_application_and_receipts() -> None:
    assert is_article_candidate("Автор/Анкета-заявка.docx")[0] is False
    assert is_article_candidate("Автор/receipt.pdf")[0] is False


def test_article_candidate_accepts_thesis_docx() -> None:
    ok, reason = is_article_candidate("Автор/Тези_Коваленко_Микита.docx")
    assert ok is True
    assert reason == "article_hint"


def test_article_candidate_ignores_parent_application_folder() -> None:
    ok, reason = is_article_candidate("136/Заявки/26 Коваленко/Тези_Коваленко_Микита.docx")
    assert ok is True
    assert reason == "article_hint"


def test_article_candidate_rejects_templates_and_temp_files() -> None:
    assert is_article_candidate("136/Учасники/Шаблоны/Сертифікат учасника.docx")[0] is False
    assert is_article_candidate("136/Учасники/Шаблоны/._~$АНД-ТАЛАНТ.docx")[0] is False


def test_unreadable_docx_is_auditable_empty_text(tmp_path) -> None:
    from zipfile import ZipFile
    from journal_factory.ingest import extract_docx_text_from_zip

    archive = tmp_path / "bad.zip"
    with ZipFile(archive, "w") as zf:
        zf.writestr("bad.docx", b"not a docx")
    assert extract_docx_text_from_zip(archive, "bad.docx") == ""


def test_dotx_style_snapshot_reads_template_content_type() -> None:
    from pathlib import Path
    from journal_factory.template import style_snapshot

    template = Path(r"C:\Users\Vint\Desktop\Jurnal.dotx")
    if template.exists():
        snapshot = style_snapshot(template)
        assert snapshot["styles"]
