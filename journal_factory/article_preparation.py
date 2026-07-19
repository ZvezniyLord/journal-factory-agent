from __future__ import annotations

from pathlib import Path
from typing import Any
from copy import deepcopy
import hashlib
import re

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.section import CT_SectPr
from rapidfuzz.fuzz import ratio

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
    title = str(article.get("title_manifest") or article.get("title_detected") or "").strip()
    bookmark_name = _bookmark_name(str(article.get("article_id") or "")) if title else ""
    base_report = {
        "article_id": article.get("article_id"),
        "source_path": article.get("source_path"),
        "source_sha256": sha256_file(source_file),
        "transformation": "none",
        "prepared_path": str(source_file),
        "prepared_sha256": sha256_file(source_file),
        "removed_body_elements": 0,
        "removed_section_properties": 0,
        "removed_trailing_empty_paragraphs": 0,
        "title_bookmark": bookmark_name,
        "title_paragraph_index": None,
        "title_match_source": "",
        "title_match_score": 0.0,
        "preserved_article_text": True,
        "blockers": [],
        "status": "PASS",
    }
    document = Document(str(source_file))
    body_elements = [element for element in document.element.body if not isinstance(element, CT_SectPr)]
    removed_body_elements = 0
    transformations: list[str] = []
    expected_article_text = extract_docx_evidence_text(source_file)

    if embedded_tail:
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
        removed_body_elements = len(removed)
        transformations.append("remove_embedded_application_tail")

    removed_section_properties = 0
    for sect_pr in list(document.element.body.xpath(".//w:pPr/w:sectPr")):
        sect_pr.getparent().remove(sect_pr)
        removed_section_properties += 1
    if removed_section_properties:
        transformations.append("remove_article_section_properties")

    removed_trailing_empty_paragraphs = _trim_trailing_empty_paragraphs(document)
    if removed_trailing_empty_paragraphs:
        transformations.append("remove_trailing_empty_paragraphs")

    title_paragraph_index: int | None = None
    if title:
        title_match = _find_title_paragraphs(document, article)
        if title_match is None:
            base_report["blockers"] = ["article_title_paragraph_not_found"]
            base_report["status"] = "BLOCKED"
            return source_file, base_report
        title_paragraph_index = title_match["start_index"]
        title_paragraphs = title_match["paragraphs"]
        title_paragraph = _merge_title_paragraphs(title_paragraphs)
        if len(title_paragraphs) > 1:
            transformations.append("merge_split_article_title")
        _add_bookmark(title_paragraph._p, bookmark_name, article.get("journal_order"))
        transformations.append("add_article_title_bookmark")

    if not transformations:
        return source_file, base_report

    output_dir.mkdir(parents=True, exist_ok=True)
    prepared_path = output_dir / f"{article['article_id']}.docx"
    document.save(prepared_path)
    prepared_text = extract_docx_evidence_text(prepared_path)
    preserved = normalize_visible_text(expected_article_text) == normalize_visible_text(prepared_text)
    blockers = [] if preserved else ["article_prefix_changed_during_service_tail_removal"]
    report = {
        **base_report,
        "transformation": "+".join(transformations),
        "prepared_path": str(prepared_path),
        "prepared_sha256": sha256_file(prepared_path),
        "removed_body_elements": removed_body_elements,
        "removed_section_properties": removed_section_properties,
        "removed_trailing_empty_paragraphs": removed_trailing_empty_paragraphs,
        "service_marker": "АНКЕТА УЧАСНИКА" if embedded_tail else "",
        "title_bookmark": bookmark_name,
        "title_paragraph_index": title_paragraph_index,
        "title_match_source": title_match["source"] if title else "",
        "title_match_score": title_match["score"] if title else 0.0,
        "expected_article_text_sha256": _text_sha256(normalize_visible_text(expected_article_text)),
        "prepared_text_sha256": _text_sha256(normalize_visible_text(prepared_text)),
        "preserved_article_text": preserved,
        "blockers": blockers,
        "status": "PASS" if not blockers else "BLOCKED",
    }
    return prepared_path, report


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _trim_trailing_empty_paragraphs(document: Document) -> int:
    removed = 0
    for element in list(reversed(document.element.body)):
        if isinstance(element, CT_SectPr):
            continue
        if element.tag != qn("w:p"):
            break
        text = "".join(element.xpath(".//w:t/text()")).strip()
        protected = element.xpath(
            ".//w:br | .//w:instrText | .//w:fldSimple | .//w:drawing | .//w:pict | "
            ".//w:object | .//w:bookmarkStart | ./w:pPr/w:sectPr"
        )
        if text or protected:
            break
        element.getparent().remove(element)
        removed += 1
    return removed


def _bookmark_name(article_id: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", article_id.upper())
    return f"JF_{normalized}_START"


def _add_bookmark(paragraph: Any, name: str, journal_order: Any) -> None:
    bookmark_id = str(1000 + int(journal_order or 0))
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), bookmark_id)
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), bookmark_id)
    ppr = paragraph.find(qn("w:pPr"))
    if ppr is None:
        paragraph.insert(0, start)
    else:
        ppr.addnext(start)
    paragraph.append(end)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _normalize_title(value: str) -> str:
    value = re.sub(r"[^\w\sА-Яа-яІіЇїЄєҐґ]", " ", value.casefold())
    return re.sub(r"\s+", " ", value).strip()


def _find_title_paragraphs(document: Document, article: dict[str, Any]) -> dict[str, Any] | None:
    paragraphs = [
        (index, paragraph)
        for index, paragraph in enumerate(document.paragraphs[:40])
        if paragraph.text.strip()
    ]
    candidates = (
        ("manifest", str(article.get("title_manifest") or ""), 0.9),
        ("detected", str(article.get("title_detected") or ""), 0.98),
    )
    for source, expected, threshold in candidates:
        normalized_expected = _normalize_title(expected)
        if not normalized_expected:
            continue
        best: tuple[float, int, int] | None = None
        for start in range(len(paragraphs)):
            for length in range(1, 4):
                window = paragraphs[start : start + length]
                if len(window) != length:
                    continue
                combined = _normalize_title(" ".join(paragraph.text for _, paragraph in window))
                score = ratio(normalized_expected, combined) / 100.0
                candidate = (score, -length, -start)
                if best is None or candidate > (best[0], -best[2], -best[1]):
                    best = (score, start, length)
        if best is not None and best[0] >= threshold:
            selected = paragraphs[best[1] : best[1] + best[2]]
            return {
                "source": source,
                "score": round(best[0], 3),
                "start_index": selected[0][0],
                "paragraphs": [paragraph for _, paragraph in selected],
            }
    return None


def _merge_title_paragraphs(paragraphs: list[Any]) -> Any:
    first = paragraphs[0]
    for paragraph in paragraphs[1:]:
        spacer = OxmlElement("w:r")
        text = OxmlElement("w:t")
        text.set(qn("xml:space"), "preserve")
        text.text = " "
        spacer.append(text)
        first._p.append(spacer)
        for child in list(paragraph._p):
            if child.tag == qn("w:pPr"):
                continue
            first._p.append(deepcopy(child))
        paragraph._p.getparent().remove(paragraph._p)
    return first
