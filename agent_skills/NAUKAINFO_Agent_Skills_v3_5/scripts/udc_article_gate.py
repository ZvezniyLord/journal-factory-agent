#!/usr/bin/env python3
"""Article-scoped UDC detection helpers for NAUKAINFO journals."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

UDC_MARKER_RE = re.compile(r"^(?:УДК|UDC)\s*[:.]?\s*\S", re.I)
DOI_MARKER_RE = re.compile(r"^DOI\s*:", re.I)
TITLE_STYLE_NAMES = {"Назва1"}
TITLE_STYLE_IDS = {"11"}
HEADER_STYLE_NAMES = {"UDC", "AUTOR", "pip", "Normal", "SECTION"}


def style_name(paragraph) -> str:
    return paragraph.style.name if paragraph.style is not None else ""


def style_id(paragraph) -> str:
    return paragraph.style.style_id if paragraph.style is not None else ""


def is_title(paragraph) -> bool:
    return style_name(paragraph) in TITLE_STYLE_NAMES or style_id(paragraph) in TITLE_STYLE_IDS


def is_udc_marker(text: str) -> bool:
    return bool(UDC_MARKER_RE.match((text or "").strip()))


def is_doi_marker(text: str) -> bool:
    return bool(DOI_MARKER_RE.match((text or "").strip()))


def header_bounds(paragraphs: Sequence, title_index: int) -> tuple[int, int]:
    """Return [start, title_index) for the contiguous frontmatter block.

    Blank paragraphs and canonical header styles are allowed. Scanning stops at
    the previous title or the first non-header, non-empty paragraph. This keeps
    UDC detection local to one article instead of accepting a UDC elsewhere in
    a multi-article journal.
    """
    j = title_index - 1
    while j >= 0:
        p = paragraphs[j]
        text = p.text.strip()
        if is_title(p) or style_name(p) == "SECTION":
            break
        if text and style_name(p) not in HEADER_STYLE_NAMES and not is_doi_marker(text):
            break
        j -= 1
    return j + 1, title_index


def article_records(paragraphs: Sequence) -> list[dict]:
    records = []
    article_no = 0
    for title_index, p in enumerate(paragraphs):
        if not is_title(p):
            continue
        article_no += 1
        start, end = header_bounds(paragraphs, title_index)
        header = list(paragraphs[start:end])
        marker_offsets = [i for i, q in enumerate(header) if is_udc_marker(q.text)]
        markers = [header[i].text.strip() for i in marker_offsets]
        records.append(
            {
                "article_no": article_no,
                "title_index": title_index,
                "title": p.text.strip(),
                "header_start": start,
                "header_end": end,
                "udc_marker_offsets": marker_offsets,
                "udc_markers": markers,
            }
        )
    return records


def audit_udc_per_article(paragraphs: Sequence) -> list[dict]:
    defects = []
    for rec in article_records(paragraphs):
        count = len(rec["udc_markers"])
        if count == 0:
            defects.append(
                {
                    "code": "ARTICLE_UDC_MISSING",
                    "article_no": rec["article_no"],
                    "title_index": rec["title_index"],
                    "title": rec["title"],
                }
            )
        elif count > 1:
            defects.append(
                {
                    "code": "ARTICLE_UDC_DUPLICATE",
                    "article_no": rec["article_no"],
                    "title_index": rec["title_index"],
                    "title": rec["title"],
                    "markers": rec["udc_markers"],
                }
            )
        else:
            offset = rec["udc_marker_offsets"][0]
            absolute = rec["header_start"] + offset
            # A DOI line may use the same visual style, but only literal UDC/УДК
            # text counts as the mandatory marker.
            # The actual marker must use the canonical UDC paragraph style.
            # Style-name check is used because the template's title style has a
            # nonsemantic styleId and style names are the stable business label.
            p = paragraphs[absolute]
            if style_name(p) != "UDC":
                defects.append(
                    {
                        "code": "ARTICLE_UDC_WRONG_STYLE",
                        "article_no": rec["article_no"],
                        "title_index": rec["title_index"],
                        "title": rec["title"],
                        "paragraph": absolute,
                        "style": style_name(p),
                        "text": p.text.strip(),
                    }
                )
    return defects
