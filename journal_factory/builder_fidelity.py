from __future__ import annotations

from collections import Counter
import re
from typing import Any


def normalize_visible_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def audit_sources_in_final(source_snapshots: list[dict[str, Any]], final_snapshot: dict[str, Any]) -> dict[str, Any]:
    """Verify that each complete source article survives in the composed DOCX.

    This first gate is intentionally strict: the normalized full visible text of
    every source must occur exactly once in the final document.
    """
    final_text = normalize_visible_text(final_snapshot.get("visible_text", ""))
    article_results: list[dict[str, Any]] = []
    blockers: list[str] = []

    for snapshot in source_snapshots:
        source_path = snapshot.get("source_path", "")
        source_text = normalize_visible_text(snapshot.get("visible_text", ""))
        occurrences = final_text.count(source_text) if source_text else 0
        status = "PASS" if occurrences == 1 else "BLOCKED"
        if occurrences == 0:
            blockers.append(f"source_text_missing:{source_path}")
        elif occurrences > 1:
            blockers.append(f"source_text_duplicated:{source_path}:{occurrences}")
        article_results.append(
            {
                "source_path": source_path,
                "source_sha256": snapshot.get("source_sha256"),
                "normalized_text_length": len(source_text),
                "occurrences_in_final": occurrences,
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

    unsupported_sources = []
    for snapshot in source_snapshots:
        reasons = []
        if snapshot.get("charts"):
            reasons.append("charts_require_part_hash_audit")
        if snapshot.get("OLE"):
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
        },
        "unsupported_sources": unsupported_sources,
        "blockers": blockers,
    }
