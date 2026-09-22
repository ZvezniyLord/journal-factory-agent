from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .article_matcher import deterministic_match


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().casefold()
    return text in {"1", "true", "yes", "так", "да", "+", "вільний слухач", "free listener"}


def build_manifest(
    excel_report: dict[str, Any],
    source_index: dict[str, Any],
    *,
    auto_accept: float = 0.96,
) -> dict[str, Any]:
    source_records = source_index.get("records", [])
    materials: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    for row in excel_report.get("rows", []):
        semantic = row.get("semantic", {})
        excel_row = row.get("excel_row")
        title = semantic.get("title")
        authors = semantic.get("authors")
        section = semantic.get("section")
        free_listener = _truthy(semantic.get("free_listener"))

        item = {
            "excel_row": excel_row,
            "authors_raw": authors,
            "title_raw": title,
            "section_raw": section,
            "free_listener": free_listener,
            "matched_source": None,
            "match_status": None,
            "match_score": None,
            "match_candidates": [],
        }

        if free_listener:
            item["match_status"] = "FREE_LISTENER"
            materials.append(item)
            continue

        if not title:
            item["match_status"] = "REVIEW"
            issues.append({
                "code": "MISSING_REGISTRY_TITLE",
                "excel_row": excel_row,
            })
            materials.append(item)
            continue

        result = deterministic_match(
            str(title),
            source_records,
            auto_accept=auto_accept,
        )
        item["match_status"] = result["status"]
        item["matched_source"] = result.get("match")
        item["match_score"] = result.get("score")
        item["match_candidates"] = result.get("candidates", [])
        materials.append(item)

        if result["status"] != "MATCHED":
            issues.append({
                "code": "ARTICLE_MATCH_REVIEW",
                "excel_row": excel_row,
                "title": title,
                "status": result["status"],
                "candidates": result.get("candidates", []),
            })

    matched_sources = {
        item["matched_source"]
        for item in materials
        if item.get("matched_source")
    }
    all_sources = {
        record.get("path")
        for record in source_records
        if record.get("path")
    }
    unused_sources = sorted(all_sources - matched_sources)

    return {
        "registry_sheet": excel_report.get("sheet"),
        "participant_rows": len(excel_report.get("rows", [])),
        "source_docx_count": source_index.get("docx_count", 0),
        "legacy_doc_count": source_index.get("legacy_doc_count", 0),
        "materials": materials,
        "unused_sources": unused_sources,
        "issues": issues,
        "summary": {
            "matched": sum(1 for x in materials if x["match_status"] == "MATCHED"),
            "free_listeners": sum(1 for x in materials if x["match_status"] == "FREE_LISTENER"),
            "review": sum(1 for x in materials if x["match_status"] in {"REVIEW", "UNMATCHED"}),
            "unused_sources": len(unused_sources),
        },
    }


def write_manifest(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
