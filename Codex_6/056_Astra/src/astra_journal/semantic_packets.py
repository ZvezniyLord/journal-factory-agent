from __future__ import annotations

import json
from typing import Any


SEMANTIC_PACKET_VERSION = "1"


def _compact_text(value: Any, limit: int = 600) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def deterministic_facts(source_record: dict[str, Any]) -> dict[str, Any]:
    signals = source_record.get("semantic_signals") or {}
    role_hits = signals.get("role_hits") or []
    by_role: dict[str, list[dict[str, Any]]] = {}
    for hit in role_hits:
        role = str(hit.get("role") or "")
        if not role:
            continue
        by_role.setdefault(role, []).append(
            {
                "index": hit.get("index"),
                "text": _compact_text(hit.get("text")),
                "confidence": hit.get("confidence"),
            }
        )

    ref_titles = by_role.get("REF_TITLE", [])
    return {
        "udc_present": bool(by_role.get("UDC")),
        "doi_present": bool(by_role.get("DOI")),
        "orcid_present": bool(by_role.get("ORCID")),
        "supervisor_label_present": bool(by_role.get("SUPERVISOR")),
        "abstract_label_present": bool(by_role.get("ABSTRACT")),
        "keywords_label_present": bool(by_role.get("KEYWORDS")),
        "table_caption_count": len(by_role.get("TABLE_CAPTION", [])),
        "figure_caption_count": len(by_role.get("FIGURE_CAPTION", [])),
        "reference_heading_count": len(ref_titles),
        "reference_headings": ref_titles[:5],
        "role_counts": signals.get("role_counts", {}),
    }


def build_article_semantic_packet(
    manifest_item: dict[str, Any],
    source_record: dict[str, Any],
    *,
    max_chars: int = 16000,
) -> dict[str, Any]:
    signals = source_record.get("semantic_signals") or {}
    packet: dict[str, Any] = {
        "packet_version": SEMANTIC_PACKET_VERSION,
        "registry": {
            "excel_row": manifest_item.get("excel_row"),
            "authors_raw": _compact_text(manifest_item.get("authors_raw"), 400),
            "coauthors_raw": [
                _compact_text(x, 400)
                for x in manifest_item.get("coauthors_raw", [])[:10]
            ],
            "title_raw": _compact_text(manifest_item.get("title_raw"), 500),
            "section_raw": _compact_text(manifest_item.get("section_raw"), 300),
        },
        "source": {
            "path": source_record.get("path"),
            "sha256": source_record.get("sha256"),
            "paragraph_count": source_record.get("paragraph_count"),
            "table_count": source_record.get("table_count"),
            "media_count": source_record.get("media_count"),
            "hyperlink_count": source_record.get("hyperlink_count"),
            "title_candidates": [
                _compact_text(x, 500)
                for x in source_record.get("title_candidates", [])[:8]
            ],
        },
        "deterministic": deterministic_facts(source_record),
        "head": list(signals.get("head") or [])[:24],
        "tail": list(signals.get("tail") or [])[-18:],
        "role_hits": list(signals.get("role_hits") or [])[:80],
    }

    # Keep a hard request-size ceiling. Trim least valuable context first while
    # preserving registry data, deterministic facts, and the article head.
    def encoded_len() -> int:
        return len(json.dumps(packet, ensure_ascii=False, separators=(",", ":")))

    while encoded_len() > max_chars and packet["tail"]:
        packet["tail"].pop(0)
    while encoded_len() > max_chars and len(packet["role_hits"]) > 20:
        packet["role_hits"].pop()
    while encoded_len() > max_chars and len(packet["head"]) > 12:
        packet["head"].pop()

    if encoded_len() > max_chars:
        raise ValueError(
            f"Semantic packet exceeds hard limit {max_chars} chars after trimming"
        )

    packet["input_chars"] = 0
    final_size = encoded_len()
    packet["input_chars"] = final_size
    final_size = encoded_len()
    if final_size > max_chars:
        raise ValueError(
            f"Semantic packet exceeds hard limit {max_chars} chars with metadata"
        )
    packet["input_chars"] = final_size
    return packet


def article_semantic_instruction(packet: dict[str, Any]) -> str:
    return (
        "Analyze ONE scientific article only. "
        "Do not rewrite scientific content and do not invent metadata. "
        "Use registry data as matching evidence and source signals as article evidence. "
        "Return JSON only using the generic Hermes envelope. "
        "The envelope task must be 'article_semantic_audit'. "
        "result must contain: source_path, author, coauthors, supervisor, affiliation, "
        "position_degree, orcid, title, udc_status, abstract_status, keywords_status, "
        "table_caption_count, figure_caption_count, ref_title, references_region, "
        "section_raw, section_mapping_status, ambiguities. "
        "For unresolved fields use null or status='review'; never guess. "
        "Final section names must be English only, but do not invent an unapproved "
        "canonical section name. "
        "Recognize bibliography heading variants such as REFERENS/REFERENCE/BIBLIOGRAPHY "
        "but only report the needed normalization; do not edit the DOCX. "
        "Evidence should cite paragraph indexes from this packet where possible.\n"
        + json.dumps(packet, ensure_ascii=False, separators=(",", ":"))
    )
