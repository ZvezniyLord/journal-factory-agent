from pathlib import Path
import json

from journal_factory.section_normalization import resolve_article_sections


def test_sections_use_canonical_catalog_and_participant_fallback(tmp_path: Path) -> None:
    catalog = tmp_path / "sections.json"
    catalog.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sections": [
                    {"order": 34, "label_uk": "Педагогіка та освіта", "label_en": "Pedagogy and Education"},
                    {"order": 36, "label_uk": "Медичні науки та громадське здоров’я", "label_en": "Medical Sciences and Public Health"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    participant_dir = tmp_path / "participants"
    participant_dir.mkdir()
    (participant_dir / "conference.sorted.json").write_text(
        json.dumps(
            {
                "article_participants_sorted": [
                    {
                        "article_title": "A title without section",
                        "section_order": 36,
                        "is_placeholder": False,
                        "is_free_listener": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    articles = [
        {
            "article_id": "article-001",
            "journal_order": 1,
            "section_raw": "34.\u00a0Педагогіка та освіта",
            "section_id": "Педагогіка та освіта",
            "title_detected": "Pedagogy title",
        },
        {
            "article_id": "article-002",
            "journal_order": 2,
            "section_raw": "",
            "section_id": "",
            "title_detected": "A title without section",
        },
    ]

    report = resolve_article_sections(articles, tmp_path, catalog)

    assert report["status"] == "PASS"
    assert [item["canonical_key"] for item in report["articles"]] == ["section-34", "section-36"]
    assert report["articles"][0]["display_title"] == "PEDAGOGY AND EDUCATION"
    assert report["articles"][1]["resolution_source"] == "raw_participant_manifest"
