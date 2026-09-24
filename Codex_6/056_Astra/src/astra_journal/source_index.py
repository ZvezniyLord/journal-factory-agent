from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .docx_inspector import inspect_docx_source
from .role_classifier import deterministic_role


def _likely_title_candidates(excerpt: list[dict[str, Any]]) -> list[str]:
    candidates: list[str] = []
    for record in excerpt[:30]:
        text = " ".join(str(record.get("text", "")).split())
        if not text or len(text) < 8 or len(text) > 350:
            continue
        role = deterministic_role(text)
        if role is not None and role.role.value in {
            "UDC", "DOI", "ORCID", "SUPERVISOR", "ABSTRACT",
            "KEYWORDS", "REF_TITLE", "TABLE_CAPTION", "FIGURE_CAPTION",
        }:
            continue
        style = (record.get("style_name") or "").casefold()
        runs = record.get("runs", [])
        bold_chars = sum(len(r.get("text", "")) for r in runs if r.get("bold") is True)
        uppercase_ratio = (
            sum(1 for ch in text if ch.isupper()) /
            max(1, sum(1 for ch in text if ch.isalpha()))
        )
        score = 0
        if "title" in style or "назв" in style:
            score += 3
        if bold_chars >= max(4, len(text) * 0.5):
            score += 2
        if uppercase_ratio >= 0.75:
            score += 2
        if 20 <= len(text) <= 250:
            score += 1
        if score >= 2 and text not in candidates:
            candidates.append(text)
    return candidates[:8]


def build_source_index(root: str | Path) -> dict[str, Any]:
    base = Path(root).resolve()
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for path in sorted(base.rglob("*.docx")):
        try:
            report = inspect_docx_source(path)
            report["path"] = path.relative_to(base).as_posix()
            report["title_candidates"] = _likely_title_candidates(report.get("excerpt", []))
            records.append(report)
        except Exception as exc:
            failures.append({
                "path": path.relative_to(base).as_posix(),
                "error": str(exc),
            })

    legacy_docs = [
        path.relative_to(base).as_posix()
        for path in sorted(base.rglob("*.doc"))
    ]

    return {
        "root": str(base),
        "docx_count": len(records),
        "legacy_doc_count": len(legacy_docs),
        "legacy_docs": legacy_docs,
        "records": records,
        "failures": failures,
    }


def write_source_index(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
