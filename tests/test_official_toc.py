from pathlib import Path
import json

from journal_factory.official_toc import (
    parse_official_toc_pages,
    resolve_publication_order,
)


def test_official_toc_parser_extracts_sections_articles_and_special_thanks() -> None:
    pages = [
        "COVER",
        "FRONT MATTER",
        "BIBLIOGRAPHY",
        """2
TABLE OF CONTENTS
ECONOMIC THEORY
1. Roman Reznikov
FIRST ARTICLE TITLE
6
FINANCE AND BANKING
2. Arsenii Lvovych
SECOND ARTICLE TITLE
13""",
        """3
3. Svitlana Hanziuk
THIRD ARTICLE TITLE
20
SPECIAL THANKS FOR ACTIVE PARTICIPATION ARE EXTENDED
TO THE FOLLOWING PARTICIPANTS:
One Person, Two Person""",
        "6\nECONOMIC THEORY\nUDC 330.1\nRoman Reznikov\nFIRST ARTICLE TITLE",
    ]

    report = parse_official_toc_pages(pages)

    assert report["blockers"] == []
    assert report["toc_physical_start_page"] == 4
    assert report["toc_physical_end_page"] == 5
    assert [item["ordinal"] for item in report["articles"]] == [1, 2, 3]
    assert [item["section"] for item in report["articles"]] == [
        "ECONOMIC THEORY",
        "FINANCE AND BANKING",
        "FINANCE AND BANKING",
    ]
    assert report["special_thanks"]["participants"] == ["One Person", "Two Person"]


def test_publication_resolver_replaces_participant_folder_order() -> None:
    manifest = {
        "generation_mode": "AUTO_INVENTORY_V1",
        "articles": [
            _article("article-001", 1, "Second Article Title", "Arsenii Lvovych", "b"),
            _article("article-002", 2, "First Article Title", "Roman Reznikov", "a"),
        ],
        "article_count": 2,
        "manifest_status": "PASS",
        "blockers": [],
    }
    official = {
        "extractor": "OFFICIAL_TOC_V1",
        "source": {"sha256": "f" * 64},
        "articles": [
            {
                "ordinal": 1,
                "section": "ECONOMIC THEORY",
                "authors": ["Roman Reznikov"],
                "title": "FIRST ARTICLE TITLE",
                "printed_start_page": 6,
                "physical_start_page": 8,
            },
            {
                "ordinal": 2,
                "section": "FINANCE AND BANKING",
                "authors": ["Arsenii Lvovych"],
                "title": "SECOND ARTICLE TITLE",
                "printed_start_page": 13,
                "physical_start_page": 15,
            },
        ],
    }

    updated, report = resolve_publication_order(manifest, official)

    assert report["status"] == "PASS"
    assert report["source_order_was_publication_order"] is False
    assert [item["participant_order"] for item in updated["articles"]] == [2, 1]
    assert [item["journal_order"] for item in updated["articles"]] == [1, 2]
    assert [item["article_id"] for item in updated["articles"]] == [
        "article-001",
        "article-002",
    ]


def test_conference_95_official_fixture_is_complete() -> None:
    fixture = json.loads(
        Path("fixtures/conferences/095/official_toc.json").read_text(encoding="utf-8")
    )

    assert fixture["status"] == "PASS"
    assert fixture["article_count"] == 34
    assert fixture["section_count"] == 14
    assert fixture["source"]["physical_page_count"] == 248
    assert fixture["source"]["bibliographic_page_count"] == 245
    assert fixture["articles"][0]["authors_display"].startswith("Резніков")
    assert fixture["articles"][0]["physical_start_page"] == 8
    assert fixture["articles"][0]["printed_start_page"] == 6
    assert fixture["special_thanks"]["present"] is True


def _article(
    article_id: str,
    order: int,
    title: str,
    author: str,
    source_key: str,
) -> dict:
    return {
        "article_id": article_id,
        "journal_order": order,
        "title_manifest": title,
        "title_detected": title,
        "authors_manifest": [author],
        "authors_detected": [author],
        "source_path": f"{source_key}.docx",
        "source_sha256": source_key * 64,
        "match_status": "MATCHED",
        "provenance": {},
    }
