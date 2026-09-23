from astra_journal.semantic_packets import (
    article_semantic_instruction,
    build_article_semantic_packet,
)


def _source() -> dict:
    return {
        "path": "article.docx",
        "sha256": "a" * 64,
        "paragraph_count": 100,
        "table_count": 2,
        "media_count": 1,
        "hyperlink_count": 0,
        "title_candidates": ["ARTICLE TITLE"],
        "semantic_signals": {
            "head": [
                {
                    "index": i,
                    "text": ("Header paragraph " + str(i)) * 20,
                    "style_name": "Normal",
                }
                for i in range(24)
            ],
            "tail": [
                {
                    "index": 80 + i,
                    "text": ("Tail paragraph " + str(i)) * 20,
                    "style_name": "Normal",
                }
                for i in range(18)
            ],
            "role_hits": [
                {
                    "index": 1,
                    "text": "УДК 001.1",
                    "role": "UDC",
                    "confidence": 0.995,
                    "evidence": ["udc-prefix"],
                },
                {
                    "index": 90,
                    "text": "REFERENCES",
                    "role": "REF_TITLE",
                    "confidence": 0.99,
                    "evidence": ["reference-heading"],
                },
            ],
            "role_counts": {"UDC": 1, "REF_TITLE": 1},
        },
    }


def test_article_packet_is_bounded_and_single_article() -> None:
    packet = build_article_semantic_packet(
        {
            "excel_row": 2,
            "authors_raw": "Author A",
            "coauthors_raw": ["Author B"],
            "title_raw": "ARTICLE TITLE",
            "section_raw": "Section raw",
        },
        _source(),
        max_chars=7000,
    )
    assert packet["source"]["path"] == "article.docx"
    assert packet["registry"]["coauthors_raw"] == ["Author B"]
    assert packet["deterministic"]["udc_present"] is True
    assert len(str(packet)) < 12000


def test_instruction_contains_only_one_packet() -> None:
    packet = build_article_semantic_packet(
        {
            "excel_row": 2,
            "authors_raw": "Author A",
            "title_raw": "ARTICLE TITLE",
            "section_raw": "Section raw",
        },
        _source(),
        max_chars=9000,
    )
    instruction = article_semantic_instruction(packet)
    assert instruction.count('"source_path"') == 0
    assert instruction.count('"path":"article.docx"') == 1
    assert "Analyze ONE scientific article only" in instruction
