from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re
import zipfile

from lxml import etree

from .archive_workspace import sha256_file


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": WORD_NS}


def audit_pdf_pages(pdf_path: Path, expected_page_count: int | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    pages: list[dict[str, Any]] = []
    blank_pages: list[int] = []
    missing_footer_numbers: list[int] = []
    unexpected_title_page_number = False
    try:
        import fitz
    except ImportError:
        return {
            "status": "BLOCKED",
            "renderer": "PyMuPDF raster inspection",
            "pdf": str(pdf_path),
            "blockers": ["pymupdf_unavailable"],
        }

    if not pdf_path.is_file():
        return {
            "status": "BLOCKED",
            "renderer": "PyMuPDF raster inspection",
            "pdf": str(pdf_path),
            "blockers": ["pdf_missing"],
        }

    document = fitz.open(str(pdf_path))
    try:
        page_count = document.page_count
        if expected_page_count is not None and page_count != expected_page_count:
            blockers.append(f"visual_page_count:{page_count}:expected={expected_page_count}")
        for page_index in range(page_count):
            physical_page = page_index + 1
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), alpha=False)
            samples = pixmap.samples
            nonwhite_channel_ratio = (
                (len(samples) - samples.count(b"\xff")) / len(samples) if samples else 0.0
            )
            text = page.get_text("text")
            footer_numbers: list[int] = []
            for block in page.get_text("blocks"):
                if float(block[1]) < float(page.rect.height) * 0.9:
                    continue
                for line in str(block[4]).splitlines():
                    value = line.strip()
                    if re.fullmatch(r"\d+", value):
                        footer_numbers.append(int(value))

            content_lines = [
                line.strip()
                for line in text.splitlines()
                if line.strip() and line.strip() != str(physical_page)
            ]
            content_character_count = sum(len(line) for line in content_lines)
            visually_blank = content_character_count < 10 and nonwhite_channel_ratio < 0.002
            if visually_blank:
                blank_pages.append(physical_page)
            if physical_page == 1:
                unexpected_title_page_number = 1 in footer_numbers
            elif physical_page not in footer_numbers:
                missing_footer_numbers.append(physical_page)
            pages.append(
                {
                    "physical_page": physical_page,
                    "text_character_count": len(text),
                    "content_character_count": content_character_count,
                    "nonwhite_channel_ratio": round(nonwhite_channel_ratio, 6),
                    "footer_numbers": footer_numbers,
                    "visually_blank": visually_blank,
                }
            )
    finally:
        document.close()

    if blank_pages:
        blockers.append(f"visually_blank_pages:{','.join(map(str, blank_pages))}")
    if missing_footer_numbers:
        blockers.append(
            "missing_visible_footer_numbers:" + ",".join(map(str, missing_footer_numbers))
        )
    if unexpected_title_page_number:
        blockers.append("title_page_number_not_hidden")
    representative_pages = sorted(
        {
            page
            for page in (1, 2, 3, 4, 5, 6, page_count // 4, page_count // 2, 3 * page_count // 4, page_count)
            if 1 <= page <= page_count
        }
    )
    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "renderer": "PyMuPDF raster inspection of Microsoft Word PDF",
        "pdf": str(pdf_path),
        "pdf_sha256": sha256_file(pdf_path),
        "inspected_page_count": len(pages),
        "expected_page_count": expected_page_count,
        "all_pages_inspected": len(pages) == page_count,
        "representative_full_resolution_pages": representative_pages,
        "blank_pages": blank_pages,
        "footer_page_numbers_expected": max(page_count - 1, 0),
        "footer_page_numbers_present": max(page_count - 1 - len(missing_footer_numbers), 0),
        "missing_footer_numbers": missing_footer_numbers,
        "title_page_number_hidden": not unexpected_title_page_number,
        "pages": pages,
        "blockers": blockers,
    }


def build_toc_pagination_report(
    docx_path: Path,
    render_report: dict[str, Any],
    visual_report: dict[str, Any],
    output_path: Path,
    expected_article_count: int | None = None,
    expected_first_article_page: int | None = None,
) -> dict[str, Any]:
    structure = _docx_pagination_structure(docx_path)
    toc_entries = render_report.get("toc_entries") or []
    article_entries = [item for item in toc_entries if int(item.get("level") or 0) == 2]
    bookmarks = render_report.get("article_bookmarks") or []
    mappings: list[dict[str, Any]] = []
    blockers: list[str] = []

    if int(render_report.get("word_toc_count") or 0) != 1:
        blockers.append(f"word_toc_count:{render_report.get('word_toc_count')}:expected=1")
    if int(render_report.get("stable_measurements_achieved") or 0) < 2:
        blockers.append("toc_layout_not_stable")
    if expected_article_count is not None:
        if len(article_entries) != expected_article_count:
            blockers.append(
                f"toc_article_entry_count:{len(article_entries)}:expected={expected_article_count}"
            )
        if len(bookmarks) != expected_article_count:
            blockers.append(
                f"article_bookmark_count:{len(bookmarks)}:expected={expected_article_count}"
            )
    for index, (entry, bookmark) in enumerate(zip(article_entries, bookmarks), start=1):
        toc_page = int(entry.get("page_number") or 0)
        physical_page = int(bookmark.get("physical_page") or 0)
        printed_page = int(bookmark.get("printed_page") or 0)
        matched = toc_page == physical_page == printed_page
        if not matched:
            blockers.append(f"article_page_mapping:{index}:{toc_page}:{physical_page}:{printed_page}")
        mappings.append(
            {
                "article_index": index,
                "bookmark": bookmark.get("name"),
                "toc_page": toc_page,
                "physical_page": physical_page,
                "printed_page": printed_page,
                "matched": matched,
            }
        )
    if expected_first_article_page is not None and mappings:
        first = mappings[0]
        if first["physical_page"] != expected_first_article_page or first["printed_page"] != expected_first_article_page:
            blockers.append(
                f"first_article_page:{first['physical_page']}:{first['printed_page']}:expected={expected_first_article_page}"
            )
    if structure.get("blockers"):
        blockers.extend(structure["blockers"])
    if visual_report.get("status") != "PASS":
        blockers.extend(f"visual:{item}" for item in visual_report.get("blockers") or [])

    report = {
        "status": "PASS" if not blockers else "BLOCKED",
        "docx": str(docx_path),
        "docx_sha256": sha256_file(docx_path),
        "pdf": render_report.get("output_pdf"),
        "pdf_sha256": render_report.get("output_pdf_sha256"),
        "word_toc_count": int(render_report.get("word_toc_count") or 0),
        "toc_style_mapping": {"SECTION": 1, "Назва1": 2},
        "toc_level_counts": render_report.get("toc_level_counts") or {},
        "toc_article_entry_count": len(article_entries),
        "article_bookmark_count": len(bookmarks),
        "toc_pages_match_article_starts": bool(mappings) and all(item["matched"] for item in mappings),
        "article_page_mappings": mappings,
        "first_article_page": mappings[0] if mappings else None,
        "stable_measurements_required": 2,
        "stable_measurements_achieved": int(
            render_report.get("stable_measurements_achieved") or 0
        ),
        "document_structure": structure,
        "continuous_pagination": {
            "status": visual_report.get("status"),
            "title_page_number_hidden": visual_report.get("title_page_number_hidden"),
            "footer_page_numbers_expected": visual_report.get("footer_page_numbers_expected"),
            "footer_page_numbers_present": visual_report.get("footer_page_numbers_present"),
            "missing_footer_numbers": visual_report.get("missing_footer_numbers") or [],
        },
        "blockers": blockers,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _docx_pagination_structure(docx_path: Path) -> dict[str, Any]:
    blockers: list[str] = []
    with zipfile.ZipFile(docx_path) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
        sections = root.xpath("//w:body//w:sectPr", namespaces=NS)
        section_data: list[dict[str, Any]] = []
        for index, section in enumerate(sections, start=1):
            page_types = section.xpath("./w:pgNumType", namespaces=NS)
            start = page_types[0].get(f"{{{WORD_NS}}}start") if page_types else None
            section_data.append(
                {
                    "section_index": index,
                    "page_number_start": int(start) if start is not None else None,
                    "title_page": bool(section.xpath("./w:titlePg", namespaces=NS)),
                    "header_reference_count": len(
                        section.xpath("./w:headerReference", namespaces=NS)
                    ),
                    "footer_reference_count": len(
                        section.xpath("./w:footerReference", namespaces=NS)
                    ),
                }
            )
        footer_field_count = 0
        for name in archive.namelist():
            if not re.fullmatch(r"word/footer\d+\.xml", name):
                continue
            footer = etree.fromstring(archive.read(name))
            instructions = " ".join(footer.xpath(".//w:instrText/text()", namespaces=NS))
            footer_field_count += len(re.findall(r"\bPAGE\b", instructions, flags=re.IGNORECASE))

    if not section_data:
        blockers.append("section_properties_missing")
    else:
        if section_data[0]["page_number_start"] != 1:
            blockers.append(f"first_section_page_start:{section_data[0]['page_number_start']}:expected=1")
        if not section_data[0]["title_page"]:
            blockers.append("first_section_title_page_flag_missing")
        restarted = [
            item["section_index"]
            for item in section_data[1:]
            if item["page_number_start"] is not None
        ]
        if restarted:
            blockers.append("later_section_page_restarts:" + ",".join(map(str, restarted)))
    if footer_field_count < 1:
        blockers.append("page_footer_field_missing")
    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "section_count": len(section_data),
        "sections": section_data,
        "page_footer_field_count": footer_field_count,
        "blockers": blockers,
    }
