from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any

from .archive_workspace import inventory_workspace, sha256_file
from .source_snapshot import extract_docx_evidence_text


MANIFEST_CANDIDATES = [
    "applications/manifest.json",
    "manifest.json",
    "FILE_MANIFEST.json",
]


def build_article_manifest(workspace_source: Path, reports_dir: Path) -> dict[str, Any]:
    manifest_path = _find_manifest_source(workspace_source)
    if manifest_path is None:
        result = _empty_invalid_manifest("manifest_source_missing")
        _write_manifest(reports_dir, result)
        return result
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        result = _empty_invalid_manifest(f"manifest_invalid_json:{exc.msg}")
        _write_manifest(reports_dir, result)
        return result

    records = raw.get("articles", [])
    free_raw = raw.get("free_listeners", [])
    blockers: list[str] = []
    warnings: list[str] = []
    if not isinstance(records, list):
        records = []
        blockers.append("manifest_articles_not_array")
    if not isinstance(free_raw, list):
        free_raw = []
        blockers.append("manifest_free_listeners_not_array")

    order_counts: dict[int, int] = {}
    for record in records:
        order = record.get("journal_order") if isinstance(record, dict) else None
        if isinstance(order, int):
            order_counts[order] = order_counts.get(order, 0) + 1
    duplicate_orders = sorted(order for order, count in order_counts.items() if count > 1)
    blockers.extend(f"duplicate_journal_order:{order}" for order in duplicate_orders)
    missing_orders = _missing_orders(sorted(order_counts))
    warnings.extend(f"missing_journal_order:{order}" for order in missing_orders)

    inventory = inventory_workspace(workspace_source)
    article_files = [item for item in inventory if item.article_candidate]
    texts = {
        item.path: extract_docx_evidence_text(workspace_source / item.path) if item.extension == ".docx" else ""
        for item in article_files
    }
    entries = []
    record_to_matches: dict[str, list[str]] = {}
    source_to_records: dict[str, list[str]] = {}
    for index, record in enumerate(records, start=1):
        entry = _match_record(index, record, workspace_source, article_files, texts)
        entries.append(entry)
        if entry["match_status"] == "MATCHED":
            record_to_matches.setdefault(entry["article_id"], []).append(entry["source_path"])
            source_to_records.setdefault(entry["source_path"], []).append(entry["article_id"])

    for entry in entries:
        if len(record_to_matches.get(entry["article_id"], [])) > 1:
            entry["blockers"].append("manifest_record_matches_multiple_sources")
        if entry["source_path"] and len(source_to_records.get(entry["source_path"], [])) > 1:
            entry["blockers"].append("source_article_matches_multiple_manifest_records")
        if entry["blockers"] and entry["match_status"] == "MATCHED":
            entry["match_status"] = "BLOCKED"

    free_listeners = [_free_listener(item, workspace_source, idx) for idx, item in enumerate(free_raw, start=1)]
    blockers.extend(
        f"{entry['article_id']}:{blocker}"
        for entry in entries
        for blocker in entry["blockers"]
        if blocker
    )
    result = {
        "manifest_source": manifest_path.relative_to(workspace_source).as_posix(),
        "manifest_sha256": sha256_file(manifest_path),
        "articles": entries,
        "article_count": len(entries),
        "free_listeners": free_listeners,
        "free_listener_count": len(free_listeners),
        "blockers": blockers,
        "warnings": warnings,
        "manifest_status": "PASS" if not blockers and all(e["match_status"] == "MATCHED" for e in entries) else "BLOCKED",
    }
    _write_manifest(reports_dir, result)
    return result


def _match_record(index: int, record: dict[str, Any], workspace_source: Path, article_files: list, texts: dict[str, str]) -> dict:
    article_id = str(record.get("article_id") or f"article-{index:03d}")
    authors_manifest = [str(item) for item in record.get("authors_manifest", record.get("authors", []))]
    title_manifest = str(record.get("title_manifest", record.get("title", "")))
    blockers: list[str] = []
    warnings: list[str] = []
    candidates = []
    for item in article_files:
        text = texts.get(item.path, "")
        author_score = _author_score(authors_manifest, text)
        title_score = _title_score(title_manifest, text)
        if author_score or title_score:
            candidates.append((item, author_score, title_score, text))
    matched = [candidate for candidate in candidates if candidate[1] >= 1 and candidate[2] >= 1]
    if len(matched) == 1:
        source, author_score, title_score, text = matched[0]
        status = "MATCHED"
    elif len(matched) > 1:
        source, author_score, title_score, text = matched[0]
        status = "BLOCKED"
        blockers.append("multiple_source_articles_match_record")
    else:
        source, author_score, title_score, text = (candidates[0] if candidates else (None, 0.0, 0.0, ""))
        status = "REVIEW" if candidates else "BLOCKED"
        if not candidates:
            blockers.append("no_source_article_match")
        elif author_score and not title_score:
            blockers.append("title_evidence_missing")
        elif title_score and not author_score:
            blockers.append("author_evidence_missing")
        else:
            blockers.append("independent_evidence_missing")

    source_path = source.path if source else ""
    source_file = workspace_source / source_path if source_path else None
    application_path = str(record.get("application_path") or "")
    application_file = workspace_source / application_path if application_path else None
    if application_path and not application_file.exists():
        warnings.append("application_path_missing")
    return {
        "article_id": article_id,
        "journal_order": record.get("journal_order"),
        "section_id": str(record.get("section_id", "")),
        "section_raw": str(record.get("section_raw", "")),
        "participation_type": str(record.get("participation_type", "article")),
        "source_path": source_path,
        "source_extension": source.extension if source else "",
        "source_sha256": source.sha256 if source else "",
        "application_path": application_path,
        "application_sha256": sha256_file(application_file) if application_file and application_file.exists() else "",
        "authors_manifest": authors_manifest,
        "authors_detected": _detect_authors(authors_manifest, text),
        "title_manifest": title_manifest,
        "title_detected": title_manifest if _title_score(title_manifest, text) >= 1 else "",
        "language": _detect_language(text),
        "article_candidate": bool(source),
        "match_status": status,
        "match_score": min(author_score, title_score),
        "author_score": author_score,
        "title_score": title_score,
        "evidence": {
            "author_match": author_score >= 1,
            "title_match": title_score >= 1,
            "filename_used_for_match": False,
        },
        "blockers": blockers,
        "warnings": warnings,
    }


def _free_listener(item: dict[str, Any], workspace_source: Path, index: int) -> dict:
    application_path = str(item.get("application_path") or "")
    application_file = workspace_source / application_path if application_path else None
    status = "PASS" if application_file and application_file.exists() else "REVIEW"
    return {
        "listener_id": str(item.get("listener_id") or f"listener-{index:03d}"),
        "full_name": str(item.get("full_name") or ""),
        "application_path": application_path,
        "source_sha256": sha256_file(application_file) if application_file and application_file.exists() else "",
        "evidence": ["manifest_free_listener_record"],
        "status": status,
    }


def _find_manifest_source(workspace_source: Path) -> Path | None:
    for rel in MANIFEST_CANDIDATES:
        path = workspace_source / rel
        if path.exists():
            return path
    return None


def _author_score(authors: list[str], text: str) -> float:
    normalized = _normalize(text)
    if not authors:
        return 0.0
    matches = sum(1 for author in authors if _normalize(author) and _normalize(author) in normalized)
    return 1.0 if matches == len(authors) else 0.0


def _title_score(title: str, text: str) -> float:
    normalized_title = _normalize(title)
    return 1.0 if normalized_title and normalized_title in _normalize(text) else 0.0


def _detect_authors(authors: list[str], text: str) -> list[str]:
    normalized = _normalize(text)
    return [author for author in authors if _normalize(author) in normalized]


def _detect_language(text: str) -> str:
    if re.search(r"[А-Яа-яІіЇїЄєҐґ]", text):
        return "uk"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return "unknown"


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\sА-Яа-яІіЇїЄєҐґ]", " ", value.casefold())).strip()


def _missing_orders(orders: list[int]) -> list[int]:
    if not orders:
        return []
    expected = set(range(min(orders), max(orders) + 1))
    return sorted(expected - set(orders))


def _empty_invalid_manifest(blocker: str) -> dict[str, Any]:
    return {
        "manifest_source": "",
        "manifest_sha256": "",
        "articles": [],
        "article_count": 0,
        "free_listeners": [],
        "free_listener_count": 0,
        "blockers": [blocker],
        "warnings": [],
        "manifest_status": "BLOCKED",
    }


def _write_manifest(reports_dir: Path, manifest: dict[str, Any]) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "article_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
