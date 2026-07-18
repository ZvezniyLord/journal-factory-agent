from journal_factory.builder_fidelity import audit_sources_in_final


def test_fidelity_passes_when_text_and_objects_survive_once() -> None:
    sources = [
        {
            "source_path": "article.docx",
            "source_sha256": "source-sha",
            "visible_text": "Author\nTitle\nBody text",
            "media_hashes": {"word/media/image1.png": "image-sha"},
            "tables": [{"table_index": 0}],
            "equations": 1,
            "drawings": 1,
            "charts": [],
            "OLE": [],
            "snapshot_status": "PASS",
            "blockers": [],
        }
    ]
    final = {
        "visible_text": "Front matter Author Title Body text Final page",
        "media_hashes": {"word/media/image9.png": "image-sha"},
        "tables": [{"table_index": 0}],
        "equations": 1,
        "drawings": 1,
    }

    report = audit_sources_in_final(sources, final)

    assert report["status"] == "PASS"
    assert report["blockers"] == []


def test_fidelity_blocks_missing_or_duplicated_content() -> None:
    sources = [
        {
            "source_path": "article.docx",
            "source_sha256": "source-sha",
            "visible_text": "SAME BODY",
            "media_hashes": {"word/media/image1.png": "missing-image"},
            "tables": [{"table_index": 0}],
            "equations": 0,
            "drawings": 1,
            "charts": [],
            "OLE": [],
            "snapshot_status": "PASS",
            "blockers": [],
        }
    ]
    final = {
        "visible_text": "SAME BODY SAME BODY",
        "media_hashes": {},
        "tables": [],
        "equations": 0,
        "drawings": 0,
    }

    report = audit_sources_in_final(sources, final)

    assert report["status"] == "BLOCKED"
    assert any(item.startswith("source_text_duplicated") for item in report["blockers"])
    assert any(item.startswith("media_missing") for item in report["blockers"])
    assert "tables_missing:1" in report["blockers"]
    assert "drawings_missing:1" in report["blockers"]
