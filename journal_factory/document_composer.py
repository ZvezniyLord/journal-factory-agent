from __future__ import annotations

from pathlib import Path
from typing import Any
import locale
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.section import CT_SectPr
from docxcompose.composer import Composer


TOC_STYLE_MAPPING = (("SECTION", 1), ("Назва1", 2))


def _toc_list_separator() -> str:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\International") as key:
            separator = str(winreg.QueryValueEx(key, "sList")[0]).strip()
            if separator:
                return separator
    except (ImportError, OSError):
        pass
    return ";" if locale.localeconv().get("decimal_point") == "," else ","


def toc_instruction() -> str:
    separator = _toc_list_separator()
    mapping = separator.join(
        value for style_name, level in TOC_STYLE_MAPPING for value in (style_name, str(level))
    )
    return f'TOC \\h \\z \\t "{mapping}"'


def compose_articles_into_etalon(
    master_path: Path,
    articles: list[dict[str, Any]],
    output_path: Path,
) -> dict[str, Any]:
    """Insert ordered article DOCX files after TOC and before the tail section."""
    master = Document(str(master_path))
    expected_section_count = len(master.sections)
    _ensure_toc_field(master)
    composer = Composer(master, preserve_styles=False)
    insert_index = find_article_insert_index(master)
    initial_index = insert_index
    inserted: list[dict[str, Any]] = []
    blockers: list[str] = []
    previous_section: str | None = None

    for position, article in enumerate(articles, start=1):
        source = Path(article["source_file"])
        if source.suffix.lower() != ".docx":
            blockers.append(f"unsupported_article_extension:{source}")
            continue
        if not source.is_file():
            blockers.append(f"article_source_missing:{source}")
            continue

        section = str(article.get("section") or "").strip()
        separator = _separator_document(
            add_page_break=position != 1,
            section_title=section if section and section != previous_section else None,
        )
        separator_count = _inserted_element_count(separator)
        composer.insert(insert_index, separator)
        insert_index += separator_count

        source_doc = Document(str(source))
        article_count = _inserted_element_count(source_doc)
        composer.insert(insert_index, source_doc)
        insert_index += article_count

        inserted.append(
            {
                "position": position,
                "article_id": article.get("article_id"),
                "source_file": str(source),
                "section": section,
                "title_bookmark": article.get("title_bookmark"),
                "inserted_body_elements": article_count,
            }
        )
        if section:
            previous_section = section

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if blockers:
        return {
            "status": "BLOCKED",
            "output": None,
            "toc_tail_insert_index": initial_index,
            "inserted": inserted,
            "blockers": blockers,
        }

    composer.save(str(output_path))
    structure_report = _finalize_document_structure(
        output_path,
        articles,
        expected_section_count,
    )
    if structure_report["status"] != "PASS":
        return {
            "status": "BLOCKED",
            "output": str(output_path),
            "toc_tail_insert_index": initial_index,
            "inserted": inserted,
            "inserted_count": len(inserted),
            "structure": structure_report,
            "blockers": structure_report["blockers"],
        }
    return {
        "status": "PASS",
        "output": str(output_path),
        "toc_tail_insert_index": initial_index,
        "inserted": inserted,
        "inserted_count": len(inserted),
        "structure": structure_report,
        "blockers": [],
    }


def find_article_insert_index(document: Document) -> int:
    """Find the section-break paragraph after TABLE OF CONTENTS.

    Article blocks are inserted immediately before this paragraph, preserving
    the final service-page section that follows it.
    """
    toc_seen = False
    for index, element in enumerate(document.element.body):
        if isinstance(element, CT_SectPr):
            continue
        text = "".join(element.xpath(".//w:t/text()"))
        normalized = " ".join(text.upper().split())
        if "TABLE OF CONTENTS" in normalized:
            toc_seen = True
            continue
        if toc_seen and element.xpath("./w:pPr/w:sectPr"):
            return index
    raise ValueError("ETALON insertion anchor after TABLE OF CONTENTS was not found")


def _separator_document(add_page_break: bool, section_title: str | None) -> Document:
    separator = Document()
    paragraph = separator.add_paragraph(section_title or "")
    ppr = paragraph._p.get_or_add_pPr()
    if add_page_break:
        page_break_before = OxmlElement("w:pageBreakBefore")
        ppr.append(page_break_before)
    if section_title:
        pstyle = OxmlElement("w:pStyle")
        pstyle.set(qn("w:val"), "SECTION")
        ppr.insert(0, pstyle)
    else:
        spacing = OxmlElement("w:spacing")
        spacing.set(qn("w:before"), "0")
        spacing.set(qn("w:after"), "0")
        spacing.set(qn("w:line"), "20")
        spacing.set(qn("w:lineRule"), "exact")
        ppr.append(spacing)
        paragraph_rpr = OxmlElement("w:rPr")
        for name in ("w:sz", "w:szCs"):
            size = OxmlElement(name)
            size.set(qn("w:val"), "2")
            paragraph_rpr.append(size)
        ppr.append(paragraph_rpr)
    return separator


def _inserted_element_count(document: Document) -> int:
    return sum(1 for element in document.element.body if not isinstance(element, CT_SectPr))


def _ensure_toc_field(document: Document) -> None:
    instructions = " ".join(document.element.body.xpath(".//w:instrText/text()"))
    if re_search_toc(instructions):
        return
    heading = next(
        (
            element
            for element in document.element.body
            if "TABLE OF CONTENTS" in " ".join("".join(element.xpath(".//w:t/text()")).upper().split())
        ),
        None,
    )
    if heading is None:
        raise ValueError("TABLE OF CONTENTS heading was not found")
    paragraph = OxmlElement("w:p")
    begin_run = OxmlElement("w:r")
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    begin.set(qn("w:dirty"), "true")
    begin_run.append(begin)
    instruction_run = OxmlElement("w:r")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = f" {toc_instruction()} "
    instruction_run.append(instruction)
    separate_run = OxmlElement("w:r")
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    separate_run.append(separate)
    placeholder_run = OxmlElement("w:r")
    placeholder = OxmlElement("w:t")
    placeholder.text = "Table of contents will be updated by Microsoft Word."
    placeholder_run.append(placeholder)
    end_run = OxmlElement("w:r")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    end_run.append(end)
    for element in (begin_run, instruction_run, separate_run, placeholder_run, end_run):
        paragraph.append(element)
    heading.addnext(paragraph)
    settings = document.settings.element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")


def re_search_toc(value: str) -> bool:
    return bool(re.search(r"\bTOC\b", value, flags=re.IGNORECASE))


def _finalize_document_structure(
    output_path: Path,
    articles: list[dict[str, Any]],
    expected_section_count: int,
) -> dict[str, Any]:
    document = Document(str(output_path))
    expected_bookmark_count = sum(bool(item.get("title_bookmark")) for item in articles)
    title_style_id = _style_id_by_name(document, "Назва1") if expected_bookmark_count else ""
    blockers: list[str] = []
    applied_bookmarks: list[str] = []
    for article in articles:
        bookmark_name = str(article.get("title_bookmark") or "")
        if not bookmark_name:
            continue
        starts = [
            item
            for item in document.element.body.xpath(".//w:bookmarkStart")
            if item.get(qn("w:name")) == bookmark_name
        ]
        if len(starts) != 1:
            blockers.append(f"article_bookmark_count:{bookmark_name}:{len(starts)}")
            continue
        paragraph = starts[0].getparent()
        if paragraph.tag != qn("w:p"):
            blockers.append(f"article_bookmark_not_in_paragraph:{bookmark_name}")
            continue
        ppr = paragraph.find(qn("w:pPr"))
        if ppr is None:
            ppr = OxmlElement("w:pPr")
            paragraph.insert(0, ppr)
        pstyle = ppr.find(qn("w:pStyle"))
        if pstyle is None:
            pstyle = OxmlElement("w:pStyle")
            ppr.insert(0, pstyle)
        pstyle.set(qn("w:val"), title_style_id)
        applied_bookmarks.append(bookmark_name)

    section_properties = document.element.body.xpath(".//w:sectPr")
    if len(section_properties) != expected_section_count:
        blockers.append(
            f"unexpected_section_count:{len(section_properties)}:expected={expected_section_count}"
        )
    for index, sect_pr in enumerate(section_properties):
        for reference in list(sect_pr.xpath("./w:headerReference | ./w:footerReference")):
            sect_pr.remove(reference)
        for pg_num in list(sect_pr.xpath("./w:pgNumType")):
            sect_pr.remove(pg_num)
        for title_page in list(sect_pr.xpath("./w:titlePg")):
            sect_pr.remove(title_page)
        if index == 0:
            pg_num = OxmlElement("w:pgNumType")
            pg_num.set(qn("w:start"), "1")
            sect_pr.insert(0, pg_num)
            sect_pr.append(OxmlElement("w:titlePg"))

    if section_properties:
        footer = document.sections[0].footer
        footer.is_linked_to_previous = False
        paragraph = footer.paragraphs[0]
        paragraph.clear()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _add_complex_field(paragraph, "PAGE")
        for section in document.sections[1:]:
            section.footer.is_linked_to_previous = True

    document.save(str(output_path))
    section_count = len(Document(str(output_path)).sections)
    if len(applied_bookmarks) != expected_bookmark_count:
        blockers.append(
            f"title_style_application_count:{len(applied_bookmarks)}:{expected_bookmark_count}"
        )
    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "toc_instruction": toc_instruction(),
        "toc_style_mapping": dict(TOC_STYLE_MAPPING),
        "toc_style_separator": _toc_list_separator(),
        "title_style_id": title_style_id,
        "title_styles_applied": len(applied_bookmarks),
        "article_bookmarks": applied_bookmarks,
        "section_count": section_count,
        "page_number_policy": {
            "first_section_start": 1,
            "title_page_number_hidden": True,
            "later_sections_continue": True,
            "footer_field": "PAGE",
        },
        "blockers": blockers,
    }


def _style_id_by_name(document: Document, style_name: str) -> str:
    for style in document.styles:
        if style.name == style_name or style.style_id == style_name:
            return style.style_id
    raise ValueError(f"Required paragraph style was not found: {style_name}")


def _add_complex_field(paragraph: Any, instruction: str) -> None:
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, separate, text, end):
        paragraph.add_run()._r.append(element)
