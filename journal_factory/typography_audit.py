from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import hashlib
import json
import re
import zipfile

from lxml import etree

from .archive_workspace import sha256_file
from .typography_profile import load_typography_profile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NS = {"w": W_NS, "m": M_NS}
W_VAL = f"{{{W_NS}}}val"
W_STYLE_ID = f"{{{W_NS}}}styleId"
SPECIALIZED_STYLE_MARKERS = (
    "author",
    "autor",
    "caption",
    "footnote",
    "heading",
    "reference",
    "section",
    "title",
    "toc",
    "udc",
    "назва",
    "рис",
)


def audit_effective_typography(
    docx_path: Path,
    profiles_path: Path,
    profile_name: str,
    report_path: Path | None = None,
) -> dict[str, Any]:
    profile = load_typography_profile(profiles_path, profile_name)
    target = float(profile["body_font_size_pt"])
    with zipfile.ZipFile(docx_path) as package:
        document = etree.fromstring(package.read("word/document.xml"))
        styles = etree.fromstring(package.read("word/styles.xml"))
        footnotes = (
            etree.fromstring(package.read("word/footnotes.xml"))
            if "word/footnotes.xml" in package.namelist()
            else None
        )

    style_map, style_names, default_size = _style_catalog(styles)
    paragraphs = document.xpath("./w:body//w:p", namespaces=NS)
    bookmark_positions: list[tuple[int, str]] = []
    for index, paragraph in enumerate(paragraphs):
        names = [
            str(item)
            for item in paragraph.xpath(".//w:bookmarkStart/@w:name", namespaces=NS)
            if str(item).startswith("JF_ARTICLE_")
        ]
        bookmark_positions.extend((index, name) for name in names)

    blockers: list[str] = []
    if not bookmark_positions:
        blockers.append("article_title_bookmarks_missing")
    first_article = min((index for index, _ in bookmark_positions), default=len(paragraphs))
    last_service_break = max(
        (
            index
            for index, paragraph in enumerate(paragraphs)
            if index > first_article and paragraph.xpath("./w:pPr/w:sectPr", namespaces=NS)
        ),
        default=len(paragraphs),
    )

    effective_counts: Counter[str] = Counter()
    exception_counts: Counter[str] = Counter()
    paragraph_mark_size_counts: Counter[str] = Counter()
    exceptions: list[dict[str, Any]] = []
    sampled_paragraphs = 0
    sampled_runs = 0
    active_article = ""
    bookmark_by_position = {position: name for position, name in bookmark_positions}

    for index, paragraph in enumerate(paragraphs[first_article:last_service_break], start=first_article):
        if index in bookmark_by_position:
            active_article = bookmark_by_position[index]
        style_id = _paragraph_style_id(paragraph)
        style_name = style_names.get(style_id, style_id)
        paragraph_mark_size = _size(paragraph.find("w:pPr/w:rPr/w:sz", namespaces=NS))
        if paragraph_mark_size is not None:
            paragraph_mark_size_counts[f"{paragraph_mark_size:g}"] += 1
        inherited_size = _inherited_run_size(style_id, style_map, default_size)
        text_runs = paragraph.xpath(".//w:r[.//w:t]", namespaces=NS)
        if text_runs:
            sampled_paragraphs += 1
        for run in text_runs:
            sampled_runs += 1
            direct_size = _size(run.find("w:rPr/w:sz", namespaces=NS))
            effective = direct_size if direct_size is not None else inherited_size
            category = _exception_category(run, style_name, direct_size, effective, target)
            if category:
                exception_counts[category] += 1
                if len(exceptions) < 100:
                    text = "".join(run.xpath(".//w:t/text()", namespaces=NS))
                    exceptions.append(
                        {
                            "article_bookmark": active_article,
                            "paragraph_index": index,
                            "style": style_name,
                            "effective_size_pt": effective,
                            "category": category,
                            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        }
                    )
                continue
            key = "unresolved" if effective is None else f"{effective:g}"
            effective_counts[key] += 1
            if effective is None:
                blockers.append(f"effective_font_size_unresolved:paragraph={index}:style={style_name}")
            elif abs(effective - target) > 0.01:
                blockers.append(
                    f"effective_body_font_size_mismatch:paragraph={index}:style={style_name}:actual={effective:g}:expected={target:g}"
                )

    footnote_run_count = 0
    if footnotes is not None:
        footnote_run_count = len(footnotes.xpath(".//w:r[.//w:t]", namespaces=NS))
        if footnote_run_count:
            exception_counts["footnote"] += footnote_run_count

    blockers = list(dict.fromkeys(blockers))
    report = {
        "status": "PASS" if not blockers else "BLOCKED",
        "docx": str(docx_path),
        "docx_sha256": sha256_file(docx_path),
        "profile": profile_name,
        "expected_body_font_size_pt": profile["body_font_size_pt"],
        "default_effective_font_size_pt": default_size,
        "article_bookmark_count": len(bookmark_positions),
        "sampled_paragraph_count": sampled_paragraphs,
        "sampled_run_count": sampled_runs,
        "effective_body_size_counts": dict(sorted(effective_counts.items())),
        "paragraph_mark_size_counts": dict(sorted(paragraph_mark_size_counts.items())),
        "exception_counts": dict(sorted(exception_counts.items())),
        "exceptions": exceptions,
        "exceptions_truncated": sum(exception_counts.values()) > len(exceptions),
        "blockers": blockers,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _style_catalog(
    styles: etree._Element,
) -> tuple[dict[str, etree._Element], dict[str, str], float | None]:
    style_map = {
        str(style.get(W_STYLE_ID)): style
        for style in styles.xpath("./w:style[@w:type='paragraph']", namespaces=NS)
        if style.get(W_STYLE_ID)
    }
    style_names = {
        style_id: str(name.get(W_VAL) or style_id)
        for style_id, style in style_map.items()
        if (name := style.find("w:name", namespaces=NS)) is not None
    }
    default_size = _size(styles.find("w:docDefaults/w:rPrDefault/w:rPr/w:sz", namespaces=NS))
    return style_map, style_names, default_size


def _paragraph_style_id(paragraph: etree._Element) -> str:
    style = paragraph.find("w:pPr/w:pStyle", namespaces=NS)
    return str(style.get(W_VAL)) if style is not None and style.get(W_VAL) else ""


def _inherited_run_size(
    style_id: str,
    style_map: dict[str, etree._Element],
    default_size: float | None,
) -> float | None:
    visited: set[str] = set()
    current = style_id
    while current and current not in visited:
        visited.add(current)
        style = style_map.get(current)
        if style is None:
            break
        style_size = _size(style.find("w:rPr/w:sz", namespaces=NS))
        if style_size is not None:
            return style_size
        based_on = style.find("w:basedOn", namespaces=NS)
        current = str(based_on.get(W_VAL)) if based_on is not None and based_on.get(W_VAL) else ""
    return default_size


def _exception_category(
    run: etree._Element,
    style_name: str,
    direct_size: float | None,
    effective_size: float | None,
    target: float,
) -> str:
    if effective_size is None or abs(effective_size - target) <= 0.01:
        return ""
    if run.xpath("ancestor::w:tbl", namespaces=NS):
        return "table"
    if run.xpath("ancestor::m:oMath | ancestor::m:oMathPara", namespaces=NS):
        return "formula"
    normalized_style = re.sub(r"\s+", " ", style_name.casefold())
    if any(marker in normalized_style for marker in SPECIALIZED_STYLE_MARKERS):
        return "specialized_style"
    if direct_size is not None:
        return "local_author_override"
    return ""


def _size(element: etree._Element | None) -> float | None:
    if element is None or not element.get(W_VAL):
        return None
    try:
        return int(str(element.get(W_VAL))) / 2
    except ValueError:
        return None
