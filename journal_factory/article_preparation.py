from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import re

from docx import Document
from docx.oxml.section import CT_SectPr

from .archive_workspace import sha256_file
from .builder_fidelity import normalize_visible_text
from .source_snapshot import extract_docx_evidence_text


APPLICATION_TAIL = re.compile(r"^\s*АНКЕТА\s+УЧАСНИКА\b", re.IGNORECASE)


def prepare_article_source(
    source_file: Path,
    article: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, dict[str, Any]]:
    embedded_tail = bool(article.get("provenance", {}).get("embedded_service_tail"))
    base_report = {
        "article_id": article.get("article_id"),
        "source_path": article.get("source_path"),
        "source_sha256": sha256_file(source_file),
        "transformation": "none",
        "prepared_path": str(source_file),
        "prepared_sha256": sha256_file(source_file),
        "removed_body_elements": 0,
        "preserved_article_text": True,
        "blockers": [],
        "status": "PASS",
    }
    if not embedded_tail:
        return source_file, base_report

    document = Document(str(source_file))
    body_elements = [element for element in document.element.body if not isinstance(element, CT_SectPr)]
    split_index = next(
        (
            index
            for index, element in enumerate(body_elements)
            if APPLICATION_TAIL.search("".join(element.xpath(".//w:t/text()")))
        ),
        None,
    )
    if split_index is None:
        base_report["blockers"] = ["embedded_application_marker_not_found"]
        base_report["status"] = "BLOCKED"
        return source_file, base_report

    original_text = extract_docx_evidence_text(source_file)
    match = re.search(r"(?im)^\s*АНКЕТА\s+УЧАСНИКА\b", original_text)
    expected_article_text = original_text[: match.start()] if match else ""
    removed = body_elements[split_index:]
    for element in removed:
        element.getparent().remove(element)

    output_dir.mkdir(parents=True, exist_ok=True)
    prepared_path = output_dir / f"{article['article_id']}.docx"
    document.save(prepared_path)
    prepared_text = extract_docx_evidence_text(prepared_path)
    preserved = normalize_visible_text(expected_article_text) == normalize_visible_text(prepared_text)
    blockers = [] if preserved else ["article_prefix_changed_during_service_tail_removal"]
    report = {
        **base_report,
        "transformation": "remove_embedded_application_tail",
        "prepared_path": str(prepared_path),
        "prepared_sha256": sha256_file(prepared_path),
        "removed_body_elements": len(removed),
        "service_marker": "АНКЕТА УЧАСНИКА",
        "expected_article_text_sha256": _text_sha256(normalize_visible_text(expected_article_text)),
        "prepared_text_sha256": _text_sha256(normalize_visible_text(prepared_text)),
        "preserved_article_text": preserved,
        "blockers": blockers,
        "status": "PASS" if not blockers else "BLOCKED",
    }
    return prepared_path, report


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
