from astra_journal.manifest_builder import build_manifest


def test_manifest_matches_by_title_and_skips_free_listener() -> None:
    excel = {
        "sheet": "Sheet1",
        "rows": [
            {
                "excel_row": 2,
                "semantic": {
                    "authors": "Автор 1",
                    "title": "Назва статті",
                    "section": "Секція",
                },
            },
            {
                "excel_row": 3,
                "semantic": {
                    "authors": "Слухач",
                    "free_listener": "так",
                },
            },
        ],
    }
    sources = {
        "docx_count": 1,
        "legacy_doc_count": 0,
        "records": [
            {
                "path": "article.docx",
                "title_candidates": ["НАЗВА СТАТТІ"],
            }
        ],
    }
    result = build_manifest(excel, sources, auto_accept=0.9)
    assert result["summary"]["matched"] == 1
    assert result["summary"]["free_listeners"] == 1
    assert result["materials"][0]["matched_source"] == "article.docx"


def test_manifest_skips_blank_rows_and_marks_coauthors() -> None:
    excel = {
        "sheet": "Sheet1",
        "rows": [
            {
                "excel_row": 2,
                "semantic": {
                    "authors": "Автор 1",
                    "title": "Спільна назва",
                    "section": "Section A",
                },
            },
            {
                "excel_row": 3,
                "semantic": {
                    "authors": "Автор 2",
                    "title": "Спільна назва",
                    "section": "Section A",
                },
            },
            {
                "excel_row": 4,
                "semantic": {},
            },
        ],
    }
    sources = {
        "docx_count": 1,
        "legacy_doc_count": 0,
        "records": [
            {
                "path": "article.docx",
                "title_candidates": ["СПІЛЬНА НАЗВА"],
            }
        ],
    }
    result = build_manifest(excel, sources, auto_accept=0.9)
    assert result["summary"]["matched"] == 1
    assert result["summary"]["coauthors"] == 1
    assert result["summary"]["skipped_blank_rows"] == 1
    assert result["materials"][1]["match_status"] == "COAUTHOR"
