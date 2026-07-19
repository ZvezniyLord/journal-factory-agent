from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
from typing import Any


def normalize_visible_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def audit_sources_in_final(source_snapshots: list[dict[str, Any]], final_snapshot: dict[str, Any]) -> dict[str, Any]:
    """Verify ordered article text and object payloads without flattening tables."""
    final_text = normalize_visible_text(final_snapshot.get("visible_text", ""))
    final_paragraphs = _paragraph_sequence(final_snapshot)
    article_results: list[dict[str, Any]] = []
    blockers: list[str] = []

    for snapshot in source_snapshots:
        source_path = snapshot.get("source_path", "")
        source_text = normalize_visible_text(snapshot.get("visible_text", ""))
        source_paragraphs = _paragraph_sequence(snapshot)
        if source_paragraphs and final_paragraphs:
            occurrences = _sequence_occurrences(final_paragraphs, source_paragraphs)
            audit_method = "ordered_paragraph_sequence"
        else:
            occurrences = final_text.count(source_text) if source_text else 0
            audit_method = "normalized_visible_text_fallback"
        status = "PASS" if occurrences == 1 else "BLOCKED"
        if occurrences == 0:
            blockers.append(f"source_paragraph_sequence_missing:{source_path}")
        elif occurrences > 1:
            blockers.append(f"source_paragraph_sequence_duplicated:{source_path}:{occurrences}")
        article_results.append(
            {
                "source_path": source_path,
                "source_sha256": snapshot.get("source_sha256"),
                "normalized_text_length": len(source_text),
                "occurrences_in_final": occurrences,
                "audit_method": audit_method,
                "paragraph_count": len(source_paragraphs),
                "status": status,
            }
        )

    expected_media = Counter(
        digest
        for snapshot in source_snapshots
        for digest in snapshot.get("media_hashes", {}).values()
    )
    final_media = Counter(final_snapshot.get("media_hashes", {}).values())
    missing_media: list[dict[str, Any]] = []
    for digest, expected_count in sorted(expected_media.items()):
        actual_count = final_media.get(digest, 0)
        if actual_count < expected_count:
            missing_media.append(
                {
                    "sha256": digest,
                    "expected_count": expected_count,
                    "actual_count": actual_count,
                }
            )
            blockers.append(f"media_missing:{digest}:{expected_count - actual_count}")

    expected_tables = sum(len(snapshot.get("tables", [])) for snapshot in source_snapshots)
    expected_equations = sum(int(snapshot.get("equations", 0)) for snapshot in source_snapshots)
    expected_drawings = sum(int(snapshot.get("drawings", 0)) for snapshot in source_snapshots)
    actual_tables = len(final_snapshot.get("tables", []))
    actual_equations = int(final_snapshot.get("equations", 0))
    actual_drawings = int(final_snapshot.get("drawings", 0))

    if actual_tables < expected_tables:
        blockers.append(f"tables_missing:{expected_tables - actual_tables}")
    if actual_equations < expected_equations:
        blockers.append(f"equations_missing:{expected_equations - actual_equations}")
    if actual_drawings < expected_drawings:
        blockers.append(f"drawings_missing:{expected_drawings - actual_drawings}")

    expected_table_signatures = Counter(
        _table_signature(table)
        for snapshot in source_snapshots
        for table in snapshot.get("tables", [])
    )
    final_table_signatures = Counter(_table_signature(table) for table in final_snapshot.get("tables", []))
    missing_table_signatures = _missing_counter(expected_table_signatures, final_table_signatures)
    for item in missing_table_signatures:
        blockers.append(f"table_content_missing:{item['sha256']}:{item['missing_count']}")

    expected_textboxes = Counter(
        normalize_visible_text(item.get("text", ""))
        for snapshot in source_snapshots
        for item in snapshot.get("textboxes", [])
        if normalize_visible_text(item.get("text", ""))
    )
    final_textboxes = Counter(
        normalize_visible_text(item.get("text", ""))
        for item in final_snapshot.get("textboxes", [])
        if normalize_visible_text(item.get("text", ""))
    )
    missing_textboxes = _missing_counter(expected_textboxes, final_textboxes)
    for item in missing_textboxes:
        blockers.append(f"textbox_content_missing:{item['sha256']}:{item['missing_count']}")

    expected_charts = Counter(
        digest
        for snapshot in source_snapshots
        for digest in snapshot.get("chart_payload_hashes", {}).values()
    )
    final_charts = Counter(final_snapshot.get("chart_payload_hashes", {}).values())
    missing_charts = _missing_counter(expected_charts, final_charts, values_are_hashes=True)
    for item in missing_charts:
        blockers.append(f"chart_payload_missing:{item['sha256']}:{item['missing_count']}")

    expected_embeddings = Counter(
        digest
        for snapshot in source_snapshots
        for digest in snapshot.get("embedding_hashes", {}).values()
    )
    final_embeddings = Counter(final_snapshot.get("embedding_hashes", {}).values())
    missing_embeddings = _missing_counter(expected_embeddings, final_embeddings, values_are_hashes=True)
    for item in missing_embeddings:
        blockers.append(f"embedding_payload_missing:{item['sha256']}:{item['missing_count']}")

    unsupported_sources = []
    for snapshot in source_snapshots:
        reasons = []
        if snapshot.get("charts") and not snapshot.get("chart_payload_hashes"):
            reasons.append("charts_require_part_hash_audit")
        if snapshot.get("OLE") and not snapshot.get("embedding_hashes"):
            reasons.append("ole_requires_part_hash_audit")
        if snapshot.get("snapshot_status") != "PASS":
            reasons.extend(snapshot.get("blockers", []))
        if reasons:
            unsupported_sources.append({"source_path": snapshot.get("source_path"), "reasons": reasons})
            blockers.extend(f"unsupported_source:{snapshot.get('source_path')}:{reason}" for reason in reasons)

    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "articles": article_results,
        "article_count": len(article_results),
        "media": {
            "expected_unique_hashes": len(expected_media),
            "final_unique_hashes": len(final_media),
            "missing": missing_media,
        },
        "objects": {
            "tables_expected": expected_tables,
            "tables_final": actual_tables,
            "equations_expected": expected_equations,
            "equations_final": actual_equations,
            "drawings_expected": expected_drawings,
            "drawings_final": actual_drawings,
            "missing_table_signatures": missing_table_signatures,
            "missing_textboxes": missing_textboxes,
            "chart_payloads_expected": sum(expected_charts.values()),
            "chart_payloads_final": sum(final_charts.values()),
            "missing_chart_payloads": missing_charts,
            "embeddings_expected": sum(expected_embeddings.values()),
            "embeddings_final": sum(final_embeddings.values()),
            "missing_embeddings": missing_embeddings,
        },
        "unsupported_sources": unsupported_sources,
        "blockers": blockers,
    }


def _paragraph_sequence(snapshot: dict[str, Any]) -> list[str]:
    return [
        text
        for paragraph in snapshot.get("paragraphs", [])
        if (text := normalize_visible_text(paragraph.get("text", "")))
    ]


def _sequence_occurrences(haystack: list[str], needle: list[str]) -> int:
    if not needle or len(needle) > len(haystack):
        return 0
    return sum(haystack[index : index + len(needle)] == needle for index in range(len(haystack) - len(needle) + 1))


def _table_signature(table: dict[str, Any]) -> str:
    cells = [
        {
            "row": cell.get("row"),
            "cell": cell.get("cell"),
            "text": normalize_visible_text(cell.get("text", "")),
        }
        for cell in table.get("table_cells", [])
    ]
    return json.dumps(cells, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _missing_counter(
    expected: Counter,
    actual: Counter,
    *,
    values_are_hashes: bool = False,
) -> list[dict[str, Any]]:
    missing = []
    for value, expected_count in expected.items():
        missing_count = expected_count - actual.get(value, 0)
        if missing_count <= 0:
            continue
        digest = value if values_are_hashes else hashlib.sha256(str(value).encode("utf-8")).hexdigest()
        missing.append(
            {
                "sha256": digest,
                "expected_count": expected_count,
                "actual_count": actual.get(value, 0),
                "missing_count": missing_count,
            }
        )
    return sorted(missing, key=lambda item: item["sha256"])
