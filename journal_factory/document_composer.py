from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.section import CT_SectPr
from docxcompose.composer import Composer


def compose_articles_into_etalon(
    master_path: Path,
    articles: list[dict[str, Any]],
    output_path: Path,
) -> dict[str, Any]:
    """Insert ordered article DOCX files after TOC and before the tail section."""
    master = Document(str(master_path))
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
            add_page_break=True,
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
    return {
        "status": "PASS",
        "output": str(output_path),
        "toc_tail_insert_index": initial_index,
        "inserted": inserted,
        "inserted_count": len(inserted),
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
    paragraph = separator.add_paragraph()
    if add_page_break:
        paragraph.add_run().add_break(WD_BREAK.PAGE)
    if section_title:
        heading = separator.add_paragraph(section_title)
        ppr = heading._p.get_or_add_pPr()
        pstyle = OxmlElement("w:pStyle")
        pstyle.set(qn("w:val"), "SECTION")
        ppr.insert(0, pstyle)
    return separator


def _inserted_element_count(document: Document) -> int:
    return sum(1 for element in document.element.body if not isinstance(element, CT_SectPr))
