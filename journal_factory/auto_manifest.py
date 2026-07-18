from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from xml.etree import ElementTree as ET

from docx import Document
from rapidfuzz.fuzz import ratio

from .archive_workspace import InventoryFile, inventory_workspace, sha256_file
from .source_snapshot import extract_docx_evidence_text


DOCUMENT_EXTENSIONS = {".doc", ".docx"}
ARTICLE_MARKERS = {
    "udc": (r"\b(?:удк|udc)\b",),
    "doi": (r"\bdoi\s*:", r"https?://doi\.org/"),
    "annotation": (
        r"\b(?:коротка\s+)?(?:анотац\w*(?:\s+статті)?|annotation|abstract|summary|резюме)\b\s*[:.]?",
    ),
    "keywords": (r"\b(?:ключов\w*\s+слов\w*|key\s*words?|keywords)\b\s*:?",),
    "references": (
        r"(?:список\s+(?:використаних\s+)?джерел|література|references|bibliography)\s*:?",
    ),
}
FORM_PATTERNS = (
    r"анкета\s+учасника",
    r"ім.?я\s+і\s+прізвище\s+автора\s+публікації",
    r"піб\s+автора\s+публікації",
    r"назва\s+статті\s*\(або",
    r"дата\s+оплати\s+організаційного\s+внеску",
)
INFO_PATTERNS = (
    r"інформаційн\w*\s+лист",
    r"шановн\w*\s+колег",
    r"організаційн\w*\s+внесок",
)
CERTIFICATE_PATTERNS = (r"сертифікат", r"certificate")
PAYMENT_PATTERNS = (r"квитанц", r"receipt", r"оплат")
COMPILED_DIR_PARTS = {"збірник", "journal", "compiled", "output"}
APPLICATION_NAME_PATTERNS = (r"анкет", r"заявк", r"заява", r"application")
TEMP_NAME_PATTERNS = (r"^~\$", r"копія", r"\bcopy\b", r"\btmp\b", r"\btemp\b")
PLACEHOLDER_PATTERNS = (
    r"\[\s*(?:вкажіть|укажіть|insert|placeholder)",
    r"<\s*(?:вкажіть|укажіть|insert|placeholder)",
)
ROLE_OR_INSTITUTION_PATTERNS = (
    r"\b(?:аспірант|студент|магістр|доктор|кандидат|доцент|професор|вчитель|директор|асистент)\w*\b",
    r"\b(?:університет|академі|інститут|ліцей|школ|кафедр|імені|район|област|національн|державн|комунальн|department|university|institute|student|professor)\w*\b",
    r"\b(?:м\.|місто|україна|ukraine|kyiv|kharkiv|odesa)\b",
)
APPLICATION_MARKER = re.compile(r"^\s*АНКЕТА\s+УЧАСНИКА\b", re.IGNORECASE | re.MULTILINE)


def build_auto_manifest(workspace_source: Path, reports_dir: Path) -> dict[str, Any]:
    inventory = inventory_workspace(workspace_source)
    legacy_paths = [workspace_source / item.path for item in inventory if item.extension == ".doc"]
    legacy_texts, legacy_method, legacy_errors = _extract_legacy_doc_texts(legacy_paths)

    evidence_rows = [
        _inspect_file(
            item,
            workspace_source,
            legacy_texts.get(str((workspace_source / item.path).resolve()), ""),
        )
        for item in inventory
    ]
    group_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence_rows:
        if row["participant_group"]:
            group_rows[row["participant_group"]].append(row)

    selected: list[dict[str, Any]] = []
    blockers: list[str] = []
    warnings: list[str] = []
    group_reports: list[dict[str, Any]] = []

    for group_name, rows in sorted(
        group_rows.items(),
        key=lambda item: (item[1][0]["participant_order"], item[0].casefold()),
    ):
        candidates = [row for row in rows if row["classification"] == "ARTICLE_CANDIDATE"]
        applications = [record for row in rows for record in row.pop("_application_records", [])]
        selected_row, group_blockers = _resolve_group_candidates(candidates)
        blockers.extend(f"{group_name}:{item}" for item in group_blockers)

        if selected_row is not None:
            selected_row["classification"] = "ARTICLE"
            selected_row["reasons"].append("selected_once_for_participant_group")
            entry = _article_entry(selected_row, applications, len(selected) + 1, workspace_source)
            selected.append(entry)
            if entry["match_status"] != "MATCHED":
                blockers.extend(f"{entry['article_id']}:{item}" for item in entry["blockers"])

        for row in candidates:
            if row is selected_row:
                continue
            if group_blockers:
                row["classification"] = "REVIEW"
                row["reasons"].append("multiple_non_equivalent_articles_in_participant_group")
            else:
                row["classification"] = "DUPLICATE"
                row["duplicate_of"] = selected_row["path"] if selected_row else ""
                row["reasons"].append("semantic_duplicate_variant_excluded")

        group_reports.append(
            {
                "participant_group": group_name,
                "participant_order": rows[0]["participant_order"],
                "file_count": len(rows),
                "article_candidates": [row["path"] for row in candidates],
                "selected_article": selected_row["path"] if selected_row else "",
                "application_records": len(applications),
                "blockers": group_blockers,
            }
        )

    selected_groups = {entry["provenance"]["participant_group"] for entry in selected}
    for row in evidence_rows:
        if row["classification"] != "PENDING_ATTACHMENT":
            continue
        if row["participant_group"] in selected_groups or row["free_listener_folder"]:
            row["classification"] = "NON_ARTICLE"
            row["reasons"].append("attachment_in_resolved_participant_group")
        else:
            row["classification"] = "REVIEW"
            row["reasons"].append("unsupported_document_without_resolved_article")
            blockers.append(f"unresolved_attachment:{row['path']}")

    for row in evidence_rows:
        row.pop("_text", None)
        row.pop("_normalized_text", None)
        row.pop("_modified_epoch", None)
        row.pop("_application_records", None)
        row["confidence"] = round(float(row["confidence"]), 3)

    if not selected:
        blockers.append("auto_manifest_no_articles_detected")
    blockers.extend(
        f"unresolved_file:{row['path']}"
        for row in evidence_rows
        if row["classification"] in {"REVIEW", "BLOCKED"}
        and f"unresolved_attachment:{row['path']}" not in blockers
    )
    warnings.extend(f"legacy_text_extraction:{item}" for item in legacy_errors)
    warnings.extend(
        f"duplicate_excluded:{row['path']}"
        for row in evidence_rows
        if row["classification"] == "DUPLICATE"
    )

    evidence_report = {
        "generation_mode": "AUTO_INVENTORY_V1",
        "workspace_source": str(workspace_source),
        "inventory_file_count": len(inventory),
        "document_file_count": sum(item.extension in DOCUMENT_EXTENSIONS for item in inventory),
        "selected_article_count": len(selected),
        "classification_counts": dict(sorted(Counter(row["classification"] for row in evidence_rows).items())),
        "legacy_text_extraction": {
            "method": legacy_method,
            "requested_count": len(legacy_paths),
            "extracted_count": sum(bool(value) for value in legacy_texts.values()),
            "errors": legacy_errors,
        },
        "groups": group_reports,
        "files": evidence_rows,
        "blockers": blockers,
        "warnings": warnings,
        "status": "PASS" if not blockers else "BLOCKED",
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "manifest_evidence.json").write_text(
        json.dumps(evidence_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    inventory_digest = hashlib.sha256(
        json.dumps(
            [{"path": item.path, "sha256": item.sha256} for item in inventory],
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return {
        "manifest_source": "AUTO:archive_inventory",
        "manifest_sha256": inventory_digest,
        "generation_mode": "AUTO_INVENTORY_V1",
        "evidence_report": "manifest_evidence.json",
        "articles": selected,
        "article_count": len(selected),
        "free_listeners": [],
        "free_listener_count": 0,
        "blockers": blockers,
        "warnings": warnings,
        "manifest_status": "PASS" if not blockers else "BLOCKED",
    }


def _inspect_file(item: InventoryFile, workspace_source: Path, legacy_text: str) -> dict[str, Any]:
    path = workspace_source / item.path
    participant_order, participant_group, participant_name = _participant_context(item.path)
    free_listener = bool(re.search(r"\(\s*БП\s*\)", participant_group, re.IGNORECASE))
    path_normalized = _normalize(item.path)
    name_normalized = _normalize(PurePosixPath(item.path).name)
    text = extract_docx_evidence_text(path) if item.extension == ".docx" else legacy_text
    normalized_text = _normalize(text)
    search_text = re.sub(r"\s+", " ", text.casefold())
    markers = sorted(
        marker
        for marker, patterns in ARTICLE_MARKERS.items()
        if any(re.search(pattern, search_text, re.IGNORECASE) for pattern in patterns)
    )
    form_hits = sum(bool(re.search(pattern, search_text, re.IGNORECASE)) for pattern in FORM_PATTERNS)
    info_hits = sum(bool(re.search(pattern, search_text, re.IGNORECASE)) for pattern in INFO_PATTERNS)
    certificate_hits = sum(bool(re.search(pattern, search_text, re.IGNORECASE)) for pattern in CERTIFICATE_PATTERNS)
    placeholder_hits = sum(bool(re.search(pattern, search_text, re.IGNORECASE)) for pattern in PLACEHOLDER_PATTERNS)
    if item.extension == ".docx":
        application_records = _application_records(path)
    elif item.extension == ".doc":
        application_records = _legacy_application_records(legacy_text)
    else:
        application_records = []
    for record in application_records:
        record["source_path"] = item.path
    title, authors = _detect_identity(text, participant_name)
    modified_utc, modified_epoch = _docx_modified(path) if item.extension == ".docx" else ("", 0.0)
    reasons: list[str] = []
    classification = "NON_ARTICLE"
    confidence = 0.99
    embedded_service_tail = bool(form_hits >= 2 and len(markers) >= 3 and APPLICATION_MARKER.search(text))

    if item.service_file:
        reasons.append("office_or_workspace_temporary_file")
    elif _has_path_part(item.path, COMPILED_DIR_PARTS) and item.extension in DOCUMENT_EXTENSIONS:
        reasons.extend(["compiled_journal_directory", "not_an_individual_submission"])
    elif (
        "сертифікат" in path_normalized
        or "certificate" in path_normalized
        or (certificate_hits and not participant_group and len(markers) < 2)
    ):
        reasons.append("certificate_template_or_request")
    elif info_hits >= 1 and not participant_group:
        reasons.extend(["information_letter_content", "outside_participant_folder"])
    elif form_hits >= 2 and len(markers) < 3:
        reasons.extend(["participant_application_content", "article_structure_absent"])
    elif free_listener and len(markers) < 3:
        reasons.extend(["free_listener_folder", "article_structure_absent"])
    elif (
        item.extension in DOCUMENT_EXTENSIONS
        and participant_group
        and title
        and (
            (len(markers) >= 3 and len(normalized_text) >= 1500)
            or (len(markers) >= 2 and len(normalized_text) >= 3000)
            or (len(markers) >= 1 and len(normalized_text) >= 5000 and form_hits < 2)
        )
    ):
        classification = "ARTICLE_CANDIDATE"
        confidence = 0.94 if not embedded_service_tail else 0.9
        reasons.extend(["article_structure_markers", "title_detected"])
        if authors:
            reasons.append("author_identity_detected")
        else:
            reasons.append("author_identity_requires_group_resolution")
        if embedded_service_tail:
            reasons.append("embedded_application_tail_detected")
    elif item.extension == ".doc" and any(re.search(pattern, name_normalized) for pattern in APPLICATION_NAME_PATTERNS):
        reasons.extend(["legacy_document_application_name", "participant_folder_context"])
        confidence = 0.82 if participant_group else 0.9
    elif item.extension in {".pdf", ".doc", ".docx", ".odt", ".rtf"}:
        if any(re.search(pattern, name_normalized) for pattern in PAYMENT_PATTERNS):
            reasons.extend(["payment_document_name", "article_structure_absent"])
        elif item.extension == ".pdf" and participant_group:
            classification = "PENDING_ATTACHMENT"
            confidence = 0.75
            reasons.append("participant_pdf_requires_group_resolution")
        elif item.extension == ".doc" and participant_group and not text:
            classification = "PENDING_ATTACHMENT"
            confidence = 0.55
            reasons.append("legacy_document_text_unavailable")
        elif participant_group:
            classification = "REVIEW"
            confidence = 0.4
            reasons.append("document_identity_or_article_structure_insufficient")
        else:
            reasons.append("service_document_outside_participant_folder")
    else:
        reasons.append("unsupported_non_article_extension")

    if placeholder_hits:
        reasons.append("unresolved_placeholder_detected")
    if any(re.search(pattern, name_normalized) for pattern in TEMP_NAME_PATTERNS):
        reasons.append("temporary_or_copy_name_clue")

    return {
        "path": item.path,
        "extension": item.extension,
        "sha256": item.sha256,
        "participant_group": participant_group,
        "participant_order": participant_order,
        "free_listener_folder": free_listener,
        "classification": classification,
        "confidence": confidence,
        "reasons": reasons,
        "content_markers": markers,
        "text_length": len(text),
        "title_detected": title,
        "authors_detected": authors,
        "modified_utc": modified_utc,
        "embedded_service_tail": embedded_service_tail,
        "placeholder_count": placeholder_hits,
        "duplicate_of": "",
        "_text": text,
        "_normalized_text": normalized_text,
        "_modified_epoch": modified_epoch,
        "_application_records": application_records,
    }


def _resolve_group_candidates(candidates: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[str]]:
    if not candidates:
        return None, []
    if len(candidates) == 1:
        return candidates[0], []
    for left_index, left in enumerate(candidates):
        for right in candidates[left_index + 1 :]:
            similarity = ratio(left["_normalized_text"], right["_normalized_text"]) / 100.0
            if similarity < 0.97:
                return None, ["multiple_non_equivalent_article_candidates"]

    def rank(row: dict[str, Any]) -> tuple[Any, ...]:
        return (
            -row["placeholder_count"],
            row["_modified_epoch"],
            len(row["content_markers"]),
            row["text_length"],
            1 if PurePosixPath(row["path"]).name.casefold().startswith("new_") else 0,
            row["path"],
        )

    return max(candidates, key=rank), []


def _article_entry(
    row: dict[str, Any],
    applications: list[dict[str, str]],
    journal_order: int,
    workspace_source: Path,
) -> dict[str, Any]:
    application = _best_application_record(row, applications)
    title_manifest = application.get("title", "") if application else row["title_detected"]
    application_authors = application.get("authors", []) if application else []
    authors_detected = row["authors_detected"] or _application_authors_in_text(application_authors, row["_text"])
    authors_manifest = application_authors if application_authors else authors_detected
    if isinstance(authors_manifest, str):
        authors_manifest = [authors_manifest]
    section_raw = application.get("section", "") if application else ""
    title_score = _identity_similarity(title_manifest, row["_text"]) if title_manifest else 1.0
    folder_author_match = _folder_author_match(row["participant_group"], row["_text"])
    author_score = 1.0 if authors_detected and (folder_author_match or application) else 0.8
    confidence = min(float(row["confidence"]), min(title_score, author_score))
    application_path = application.get("source_path", "") if application else ""
    application_file = workspace_source / application_path if application_path else None
    blockers: list[str] = []
    if title_score < 0.9:
        blockers.append("application_title_conflicts_with_article")
    if not authors_detected:
        blockers.append("article_author_identity_missing")
    if not row["title_detected"]:
        blockers.append("article_title_missing")
    status = "MATCHED" if not blockers else "REVIEW"
    return {
        "article_id": f"article-{journal_order:03d}",
        "journal_order": journal_order,
        "section_id": _section_id(section_raw),
        "section_raw": section_raw,
        "participation_type": "article",
        "source_path": row["path"],
        "source_extension": row["extension"],
        "source_sha256": row["sha256"],
        "application_path": application_path,
        "application_sha256": sha256_file(application_file) if application_file and application_file.exists() else "",
        "authors_manifest": list(authors_manifest),
        "authors_detected": authors_detected,
        "title_manifest": title_manifest,
        "title_detected": row["title_detected"],
        "language": _detect_language(row["_text"]),
        "article_candidate": True,
        "match_status": status,
        "match_score": round(confidence, 3),
        "author_score": round(author_score, 3),
        "title_score": round(title_score, 3),
        "confidence": round(confidence, 3),
        "provenance": {
            "generation": "AUTO_INVENTORY_V1",
            "participant_group": row["participant_group"],
            "participant_order": row["participant_order"],
            "identity_sources": [
                "article_visible_text",
                "participant_folder",
                *(["application_record"] if application else []),
            ],
            "selection_reasons": row["reasons"],
            "content_markers": row["content_markers"],
            "embedded_service_tail": row["embedded_service_tail"],
        },
        "evidence": {
            "author_match": author_score >= 0.8,
            "title_match": title_score >= 0.9,
            "filename_used_for_match": False,
            "folder_used_as_supporting_evidence": bool(row["participant_group"]),
            "application_record_used": bool(application),
        },
        "blockers": blockers,
        "warnings": ["embedded_application_tail_requires_preparation"] if row["embedded_service_tail"] else [],
    }


def _best_application_record(row: dict[str, Any], applications: list[dict[str, str]]) -> dict[str, Any] | None:
    scored = []
    for application in applications:
        title = application.get("title", "")
        if not title or "вільн" in _normalize(title):
            continue
        score = _identity_similarity(title, row["_text"])
        if score >= 0.9:
            scored.append((score, application))
    if not scored:
        return None
    scored.sort(key=lambda item: (item[0], item[1].get("source_path", "")), reverse=True)
    best_score, best = scored[0]
    best_title = _normalize(best.get("title", ""))
    related = [
        application
        for score, application in scored
        if score >= 0.9
        and ratio(_normalize(application.get("title", "")), best_title) / 100.0 >= 0.95
    ]
    authors = list(
        dict.fromkeys(
            author
            for application in related
            for author in application.get("authors", [])
            if author
        )
    )
    return {
        **best,
        "authors": authors,
        "source_path": best.get("source_path", ""),
    }


def _application_records(path: Path) -> list[dict[str, Any]]:
    try:
        document = Document(str(path))
    except Exception:  # noqa: BLE001
        return []
    records: list[dict[str, Any]] = []
    for table in document.tables:
        if not table.rows:
            continue
        headers = [_normalize(cell.text) for cell in table.rows[0].cells]
        title_index = _find_header(headers, r"назва статті")
        author_index = _find_header(headers, r"(?:ім.?я і прізвище|піб) автора публікації")
        section_index = _find_header(headers, r"секці")
        if title_index is None or author_index is None:
            continue
        for row in table.rows[1:]:
            values = [re.sub(r"\s+", " ", cell.text).strip() for cell in row.cells]
            title = values[title_index] if title_index < len(values) else ""
            author = values[author_index] if author_index < len(values) else ""
            section = values[section_index] if section_index is not None and section_index < len(values) else ""
            if title and author:
                records.append(
                    {
                        "authors": [author],
                        "title": title.strip(" «»\""),
                        "section": section,
                        "source_path": "",
                    }
                )
    return records


def _find_header(headers: list[str], pattern: str) -> int | None:
    for index, value in enumerate(headers):
        if re.search(pattern, value, re.IGNORECASE):
            return index
    return None


def _detect_identity(text: str, participant_name: str) -> tuple[str, list[str]]:
    lines = [re.sub(r"\s+", " ", item).strip() for item in text.splitlines() if item.strip()]
    if not lines:
        return "", []
    boundary = next(
        (
            index
            for index, line in enumerate(lines)
            if re.search(
                r"^(?:(?:коротка\s+)?анотац\w*(?:\s+статті)?|annotation|abstract|summary|резюме|ключов\w*\s+слов\w*|key\s*words?|keywords)\b\s*[:.]?",
                line,
                re.IGNORECASE,
            )
        ),
        min(len(lines), 18),
    )
    start = next(
        (
            index + 1
            for index, line in enumerate(lines[:boundary])
            if re.search(r"\b(?:удк|udc)\b", line, re.IGNORECASE)
        ),
        0,
    )
    candidates: list[tuple[float, int, str]] = []
    for index in range(start, boundary):
        line = lines[index]
        if not _title_candidate(line):
            continue
        letters = [char for char in line if char.isalpha()]
        uppercase_ratio = sum(char.isupper() for char in letters) / len(letters) if letters else 0.0
        distance = boundary - index
        score = min(len(line), 180) / 90.0
        score += 4.0 if uppercase_ratio >= 0.7 else 0.0
        score += max(0.0, 3.0 - distance * 0.45)
        score -= (
            5.0
            if len(line) <= 90
            and any(re.search(pattern, _normalize(line), re.IGNORECASE) for pattern in ROLE_OR_INSTITUTION_PATTERNS)
            else 0.0
        )
        score -= 2.0 if line.endswith(",") else 0.0
        candidates.append((score, index, line))
    if not candidates:
        return "", _detect_authors_from_header(lines[:boundary], participant_name)
    _, title_index, title = max(candidates)
    header_lines = [*lines[start:title_index], *lines[title_index + 1 : boundary]]
    authors = _detect_authors_from_header(header_lines, participant_name)
    return title, authors


def _title_candidate(line: str) -> bool:
    normalized = _normalize(line)
    words = normalized.split()
    if not 3 <= len(words) <= 45 or not 18 <= len(line) <= 350:
        return False
    if any(
        re.search(pattern, line, re.IGNORECASE)
        for patterns in ARTICLE_MARKERS.values()
        for pattern in patterns
    ):
        return False
    if "@" in line or re.search(r"https?://", line, re.IGNORECASE):
        return False
    return True


def _detect_authors_from_header(lines: list[str], participant_name: str) -> list[str]:
    surname_tokens = _participant_surnames(participant_name)
    authors: list[str] = []
    for line in lines:
        normalized = _normalize(line)
        if not normalized or any(
            re.search(pattern, normalized, re.IGNORECASE) for pattern in ROLE_OR_INSTITUTION_PATTERNS
        ):
            continue
        if any(char.isdigit() for char in line):
            continue
        words = [word for word in re.split(r"\s+", line) if word]
        if not 2 <= len(words) <= 6:
            continue
        letters = [char for char in line if char.isalpha()]
        if len(words) > 3 and letters and sum(char.isupper() for char in letters) / len(letters) >= 0.8:
            continue
        if sum(word.strip(" ,;.")[:1].isupper() for word in words) >= 2:
            authors.append(line.strip(" ,;"))
    if authors and (
        not surname_tokens
        or any(surname.split()[0] in _normalize(" ".join(authors)) for surname in surname_tokens)
    ):
        return authors
    for surname in surname_tokens:
        surname = surname.split()[0]
        for line in lines:
            if surname not in _normalize(line):
                continue
            fragment = re.split(
                r"(?i)\b(?:аспірант|студент|магістр|доктор|кандидат|доцент|професор|вчитель|директор|асистент|student|professor)\w*",
                line,
                maxsplit=1,
            )[0].strip(" ,;")
            fragment = fragment.split(",", 1)[0].strip()
            if fragment:
                return [fragment[:160]]
    for line in lines:
        words = [word.strip(" ,;.") for word in line.split() if word.strip(" ,;.")]
        if 2 <= len(words) <= 5 and sum(word[:1].isupper() for word in words) >= 2:
            return [line.strip(" ,;")]
    return []


def _application_authors_in_text(authors: list[str], text: str) -> list[str]:
    normalized_text = _normalize(text)
    matched = []
    for author in authors:
        tokens = [token for token in _normalize(author).split() if len(token) >= 3]
        if tokens and all(token in normalized_text for token in tokens):
            matched.append(author)
    return matched


def _legacy_application_records(text: str) -> list[dict[str, Any]]:
    if "\x07" not in text:
        return []
    cells = [re.sub(r"[\r\v]+", " ", value).strip() for value in text.split("\x07")]
    first_row = next((index for index, value in enumerate(cells) if re.fullmatch(r"1\.", value)), None)
    if first_row is None:
        return []
    records: list[dict[str, Any]] = []
    index = first_row
    while index + 6 < len(cells):
        if not re.fullmatch(r"[1-5]\.", cells[index]):
            index += 1
            continue
        author = cells[index + 1]
        title = cells[index + 5]
        section = cells[index + 6]
        if author and title:
            records.append(
                {
                    "authors": [author],
                    "title": title.strip(" «»\""),
                    "section": section,
                    "source_path": "",
                }
            )
        index += 10
    return records


def _participant_context(relative_path: str) -> tuple[int, str, str]:
    parts = PurePosixPath(relative_path).parts
    for index, part in enumerate(parts[:-1]):
        if _normalize(part) not in {"заявки", "applications", "submissions"} or index + 1 >= len(parts) - 1:
            continue
        participant_part = parts[index + 1]
        match = re.match(r"^\s*(\d+)\s+(.+?)\s*$", participant_part)
        if match:
            name = re.sub(r"\s*\([^)]*\)\s*$", "", match.group(2)).strip()
            return int(match.group(1)), participant_part, name
    return 10**9, "", ""


def _participant_surnames(participant_name: str) -> list[str]:
    return [
        token
        for token in (_normalize(item) for item in re.split(r"[,/&+]", participant_name))
        if len(token) >= 3
    ]


def _folder_author_match(participant_group: str, text: str) -> bool:
    _, _, participant_name = _participant_context(f"applications/{participant_group}/file.docx")
    normalized = _normalize(text)
    surnames = _participant_surnames(participant_name)
    return bool(surnames) and all(surname.split()[0] in normalized for surname in surnames)


def _identity_similarity(expected: str, text: str) -> float:
    expected_normalized = _normalize(expected)
    text_normalized = _normalize(text)
    if not expected_normalized:
        return 0.0
    if expected_normalized in text_normalized:
        return 1.0
    lines = [line for line in text.splitlines() if line.strip()]
    return max((ratio(expected_normalized, _normalize(line)) / 100.0 for line in lines), default=0.0)


def _section_id(section: str) -> str:
    return re.sub(r"^\s*\d+[.)]?\s*", "", section).strip()


def _detect_language(text: str) -> str:
    if re.search(r"[А-Яа-яІіЇїЄєҐґ]", text):
        return "uk"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return "unknown"


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\sА-Яа-яІіЇїЄєҐґ]", " ", value.casefold())).strip()


def _has_path_part(path: str, expected: set[str]) -> bool:
    return any(_normalize(part) in expected for part in PurePosixPath(path).parts)


def _docx_modified(path: Path) -> tuple[str, float]:
    try:
        with zipfile.ZipFile(path) as package:
            root = ET.fromstring(package.read("docProps/core.xml"))
        value = next((node.text or "" for node in root if node.tag.endswith("}modified")), "")
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() if value else 0.0
        return value, timestamp
    except Exception:  # noqa: BLE001
        return "", 0.0


def _extract_legacy_doc_texts(paths: list[Path]) -> tuple[dict[str, str], str, list[str]]:
    if not paths:
        return {}, "not_needed", []
    if sys.platform != "win32":
        return {}, "unavailable", ["word_com_requires_windows"]
    with tempfile.TemporaryDirectory(prefix="journal-manifest-") as temp_dir:
        input_path = Path(temp_dir) / "input.json"
        output_path = Path(temp_dir) / "output.json"
        input_path.write_text(
            json.dumps([str(path.resolve()) for path in paths], ensure_ascii=False),
            encoding="utf-8",
        )
        script = r"""
$ErrorActionPreference = 'Stop'
$paths = Get-Content -Raw -Encoding UTF8 $env:JF_LEGACY_INPUT | ConvertFrom-Json
$results = @{}
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
try {
  foreach ($path in $paths) {
    $document = $null
    try {
      $document = $word.Documents.Open([string]$path)
      $results[[string]$path] = [string]$document.Content.Text
    } catch {
      $results[[string]$path] = ''
    } finally {
      if ($null -ne $document) { $document.Close(0) }
    }
  }
  $results | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 $env:JF_LEGACY_OUTPUT
} finally {
  $word.Quit()
}
"""
        env = dict(os.environ)
        env["JF_LEGACY_INPUT"] = str(input_path)
        env["JF_LEGACY_OUTPUT"] = str(output_path)
        try:
            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    script,
                ],
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {}, "word_com_failed", [f"{type(exc).__name__}:{exc}"]
        if completed.returncode != 0 or not output_path.exists():
            error = completed.stderr.strip().replace("\n", " ")[:500]
            return {}, "word_com_failed", [f"powershell_exit_{completed.returncode}:{error}"]
        try:
            raw = json.loads(output_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            return {}, "word_com_failed", [f"legacy_output_invalid:{type(exc).__name__}:{exc}"]
        return {str(Path(key)): str(value or "") for key, value in raw.items()}, "word_com_read_only", []
