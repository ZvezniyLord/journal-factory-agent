#!/usr/bin/env python3
"""Finalize NAUKAINFO article semantics in a merged journal without rebuilding media.

Key guarantees:
- Canonical styles are copied from Jurnal.dotx.
- Section/author/title/UDC semantics are real paragraph styles.
- Annotation and keyword labels are normalized.
- Contacts are removed from article headers without leaving empty paragraphs.
- UDC/title/references/table/figure spacing contracts are enforced.
- References are flattened to plain runs, link labels are normalized, and numbering restarts at 1 per article.
- Drawing/SmartArt/media parts are untouched.
"""
from __future__ import annotations

import argparse
import copy
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W, "r": R}
qn = lambda local: f"{{{W}}}{local}"

CANONICAL_STYLE_IDS = [
    "a0", "1", "2", "10", "20", "SECTION", "11", "AUTOR", "pip", "UDC", "UDC0",
    "ad", "af6", "TABLETEXT", "REF-TITLE", "REFER", "REFER0"
]

SECTION_LABELS = {
    "ECONOMIC THEORY, MACRO- AND REGIONAL ECONOMY",
    "CULTURE AND ARTS",
}

EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?38\s*)?\(?0\d{2}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}(?!\d)")
CONTACT_WORD_RE = re.compile(r"\b(?:телефон|контактний\s+телефон|telegram|viber|whatsapp|емейл|e-?mail)\b", re.I)
ORCID_RE = re.compile(r"orcid\.org", re.I)

ANNOTATION_RE = re.compile(r"^\s*(Анотац(?:ія|iя)|ANNOTATION|ABSTRACTS?|Abstract)\s*[:.]?\s*(.*)$", re.I | re.S)
KEYWORDS_RE = re.compile(r"^\s*(Ключові\s+слова|KEYWORDS?|Keywords?)\s*[:.]?\s*(.*)$", re.I | re.S)
REF_HEADING_RE = re.compile(r"^\s*(?:СПИСОК\s+ВИКОРИСТАН(?:ИХ\s+ДЖЕРЕЛ|ОЇ\s+ЛІТЕРАТУРИ)|ЛІТЕРАТУРА|REFERENCES?)\s*:?[\s¶]*$", re.I)
MANUAL_NUM_RE = re.compile(r"^\s*(?:\(?\d{1,3}\)?[.)]|[-–—•▪◦])\s*")
URL_RE = re.compile(r"https?://[^\s<>()]+", re.I)
BARE_DOI_RE = re.compile(r"(?<![\w/])10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)

ROLE_STARTERS_UK = (
    "Студент", "Студентка", "Здобувач", "Здобувачка", "Магістрант", "Магістрантка",
    "Аспірант", "Аспірантка", "Кандидат", "Доктор", "Доцент", "Професор", "Почесний",
    "Керівник", "Старший", "Молодший", "Науковий", "Завідувач", "Завідувачка",
    "Викладач", "Викладачка", "Асистент", "Асистентка", "Лікар", "Лікарка",
)


def read_xml(path: Path) -> etree._ElementTree:
    return etree.parse(str(path))


def write_xml(tree: etree._ElementTree, path: Path) -> None:
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone="yes")


def paragraph_text(p: etree._Element) -> str:
    parts: List[str] = []
    for node in p.iter():
        if node.tag == qn("t"):
            parts.append(node.text or "")
        elif node.tag in {qn("tab"), qn("br"), qn("cr")}:
            parts.append(" ")
    return re.sub(r"[ \t\r\f\v]+", " ", "".join(parts)).strip()


def is_p(el: etree._Element) -> bool:
    return el.tag == qn("p")


def is_tbl(el: etree._Element) -> bool:
    return el.tag == qn("tbl")


def is_blank_p(el: etree._Element) -> bool:
    return is_p(el) and not paragraph_text(el)


def get_ppr(p: etree._Element, create: bool = True) -> Optional[etree._Element]:
    ppr = p.find(qn("pPr"))
    if ppr is None and create:
        ppr = etree.Element(qn("pPr"))
        p.insert(0, ppr)
    return ppr


def set_pstyle(p: etree._Element, style_id: str) -> None:
    ppr = get_ppr(p, True)
    pstyle = ppr.find(qn("pStyle"))
    if pstyle is None:
        pstyle = etree.Element(qn("pStyle"))
        ppr.insert(0, pstyle)
    pstyle.set(qn("val"), style_id)


def get_pstyle(p: etree._Element) -> str:
    pstyle = p.find("w:pPr/w:pStyle", NS)
    return pstyle.get(qn("val")) if pstyle is not None else ""


def strip_ppr_children(p: etree._Element, keep: Sequence[str] = ()) -> None:
    ppr = get_ppr(p, True)
    keep_tags = {qn(x) for x in keep}
    for ch in list(ppr):
        if ch.tag not in keep_tags:
            ppr.remove(ch)


def make_blank_p(style_id: str = "a0") -> etree._Element:
    p = etree.Element(qn("p"))
    ppr = etree.SubElement(p, qn("pPr"))
    ps = etree.SubElement(ppr, qn("pStyle"))
    ps.set(qn("val"), style_id)
    return p


def ensure_exactly_one_blank_after(parent: etree._Element, el: etree._Element) -> etree._Element:
    idx = parent.index(el)
    while idx + 1 < len(parent) and is_blank_p(parent[idx + 1]):
        parent.remove(parent[idx + 1])
    blank = make_blank_p()
    parent.insert(idx + 1, blank)
    return blank


def ensure_exactly_one_blank_before(parent: etree._Element, el: etree._Element) -> etree._Element:
    idx = parent.index(el)
    while idx - 1 >= 0 and is_blank_p(parent[idx - 1]):
        parent.remove(parent[idx - 1])
        idx -= 1
    blank = make_blank_p()
    parent.insert(idx, blank)
    return blank


def remove_all_content_except_ppr(p: etree._Element) -> None:
    for ch in list(p):
        if ch.tag != qn("pPr"):
            p.remove(ch)


def add_run(p: etree._Element, text: str, *, bold: bool = False, italic: bool = False,
            plain: bool = False, size_half_points: int = 22) -> etree._Element:
    r = etree.SubElement(p, qn("r"))
    rpr = etree.SubElement(r, qn("rPr"))
    fonts = etree.SubElement(rpr, qn("rFonts"))
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(attr), "Times New Roman")
    sz = etree.SubElement(rpr, qn("sz")); sz.set(qn("val"), str(size_half_points))
    szcs = etree.SubElement(rpr, qn("szCs")); szcs.set(qn("val"), str(size_half_points))
    if bold:
        etree.SubElement(rpr, qn("b")); etree.SubElement(rpr, qn("bCs"))
    if italic:
        etree.SubElement(rpr, qn("i")); etree.SubElement(rpr, qn("iCs"))
    t = etree.SubElement(r, qn("t"))
    if text.startswith(" ") or text.endswith(" ") or "  " in text:
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    return r


def replace_paragraph_text(p: etree._Element, text: str, *, style_id: Optional[str] = None,
                           bold_prefix: Optional[str] = None, body_text: Optional[str] = None,
                           italic: bool = False, plain: bool = False) -> None:
    remove_all_content_except_ppr(p)
    if style_id:
        strip_ppr_children(p, keep=("pStyle", "pageBreakBefore", "numPr", "spacing", "jc", "ind", "keepNext", "keepLines"))
        set_pstyle(p, style_id)
    if bold_prefix is not None:
        add_run(p, bold_prefix, bold=True)
        if body_text:
            add_run(p, body_text, bold=False)
    else:
        add_run(p, text, italic=italic, plain=plain)


def clear_runs_to_style(p: etree._Element) -> None:
    """Clear run-level formatting like Ctrl+Space while preserving text and field/drawing nodes.

    Use only on text-only semantic paragraphs.
    """
    txt = paragraph_text(p)
    remove_all_content_except_ppr(p)
    if txt:
        r = etree.SubElement(p, qn("r"))
        t = etree.SubElement(r, qn("t"))
        if txt.startswith(" ") or txt.endswith(" "):
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = txt


def normalize_body_run(r: etree._Element, *, force_plain: bool = False) -> None:
    rpr = r.find(qn("rPr"))
    if rpr is None:
        rpr = etree.Element(qn("rPr"))
        r.insert(0, rpr)
    preserve = set()
    if not force_plain:
        for name in ("b", "bCs", "i", "iCs", "vertAlign", "strike", "dstrike", "smallCaps"):
            el = rpr.find(qn(name))
            if el is not None:
                preserve.add(name)
    for ch in list(rpr):
        if etree.QName(ch).localname not in preserve:
            rpr.remove(ch)
    fonts = etree.Element(qn("rFonts"))
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(attr), "Times New Roman")
    rpr.insert(0, fonts)
    sz = etree.SubElement(rpr, qn("sz")); sz.set(qn("val"), "22")
    szcs = etree.SubElement(rpr, qn("szCs")); szcs.set(qn("val"), "22")


def normalize_body_paragraph(p: etree._Element, *, keep_num: bool = True, zero_indent: bool = False) -> None:
    ppr = get_ppr(p, True)
    num = ppr.find(qn("numPr")) if keep_num else None
    ind = ppr.find(qn("ind")) if keep_num and num is not None else None
    jc = ppr.find(qn("jc"))
    for ch in list(ppr):
        if ch.tag == qn("pStyle"):
            continue
        if num is not None and ch is num:
            continue
        if ind is not None and ch is ind:
            continue
        if jc is not None and ch is jc:
            continue
        ppr.remove(ch)
    set_pstyle(p, "a0")
    spacing = etree.SubElement(ppr, qn("spacing"))
    spacing.set(qn("before"), "0"); spacing.set(qn("after"), "0")
    spacing.set(qn("line"), "240"); spacing.set(qn("lineRule"), "auto")
    if zero_indent:
        if ind is None:
            ind = etree.SubElement(ppr, qn("ind"))
        ind.set(qn("firstLine"), "0")
    for r in p.findall(".//w:r", NS):
        normalize_body_run(r)


def canonicalize_annotation_or_keywords(p: etree._Element) -> bool:
    txt = paragraph_text(p)
    m = ANNOTATION_RE.match(txt)
    if m:
        body = re.sub(r"\s+", " ", m.group(2).strip())
        if body and body[0].isalpha() and body[0].islower():
            body = body[0].upper() + body[1:]
        remove_all_content_except_ppr(p)
        strip_ppr_children(p, keep=("pStyle",))
        set_pstyle(p, "a0")
        add_run(p, "Анотація." if not txt.lower().startswith(("abstract", "annotation")) else "Abstract.", bold=True)
        add_run(p, " " + body if body else "")
        return True
    m = KEYWORDS_RE.match(txt)
    if m:
        body = re.sub(r"\s+", " ", m.group(2).strip())
        if body:
            token = re.split(r"[\s,;:]", body, maxsplit=1)[0]
            is_acronym = len(token) >= 2 and any(c.isalpha() for c in token) and token.upper() == token
            if not is_acronym and body[0].isalpha():
                body = body[0].lower() + body[1:]
        remove_all_content_except_ppr(p)
        strip_ppr_children(p, keep=("pStyle",))
        set_pstyle(p, "a0")
        add_run(p, "Ключові слова:" if not txt.lower().startswith("keyword") else "Keywords:", bold=True)
        add_run(p, " " + body if body else "")
        return True
    return False


def normalize_role_case(text: str) -> str:
    text = text.strip()
    for starter in ROLE_STARTERS_UK:
        if text.startswith(starter):
            text = starter[0].lower() + starter[1:] + text[len(starter):]
            break
    text = re.sub(r",\s+Заслужений\b", ", заслужений", text)
    text = re.sub(r",\s+Почесний\b", ", почесний", text)
    text = re.sub(r",\s+Керівник\b", ", керівник", text)
    return text


def strip_contact_data(text: str) -> str:
    """Remove prohibited contact data while preserving non-contact header text.

    ORCID is explicitly preserved. A paragraph that becomes empty is removed by the
    caller, so no blank hole remains in the author block.
    """
    has_contact = bool(EMAIL_RE.search(text) or PHONE_RE.search(text) or CONTACT_WORD_RE.search(text))
    if not has_contact:
        return text.strip()
    if ORCID_RE.search(text) and not (EMAIL_RE.search(text) or PHONE_RE.search(text)):
        return text.strip()
    cleaned = EMAIL_RE.sub("", text)
    cleaned = PHONE_RE.sub("", cleaned)
    cleaned = re.sub(r"\b(?:контактний\s+телефон|телефон|telegram|viber|whatsapp|емейл|e-?mail)\b\s*[:–—-]?", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*[,;|/]+\s*$", "", cleaned)
    cleaned = re.sub(r"^[\s:;,.–—-]+|[\s:;,.–—-]+$", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def is_contact_paragraph(text: str) -> bool:
    return bool((EMAIL_RE.search(text) or PHONE_RE.search(text) or CONTACT_WORD_RE.search(text)) and not strip_contact_data(text))


def has_numpr(p: etree._Element) -> bool:
    return p.find("w:pPr/w:numPr", NS) is not None


def reconstruct_reference_entries(body: etree._Element, candidate_blocks: Sequence[etree._Element]) -> List[etree._Element]:
    """Reconstruct logical bibliography entries from automatic or hand-typed numbering.

    Explicit automatic numbering or a hand-typed numeral starts an entry. Existing
    `REFER` paragraphs also start entries. A following unnumbered paragraph is merged
    into the preceding entry, covering author-created Enter/paragraph splits. When no
    reliable boundary exists, fail instead of silently collapsing the bibliography.
    """
    paragraphs = [p for p in candidate_blocks if is_p(p) and not is_blank_p(p)]
    if not paragraphs:
        return []
    has_boundaries = any(MANUAL_NUM_RE.match(paragraph_text(p)) or has_numpr(p) or get_pstyle(p) == "REFER" for p in paragraphs)
    if not has_boundaries and len(paragraphs) > 1:
        raise RuntimeError("REFERENCE_BOUNDARIES_AMBIGUOUS: manual review required")

    entries: List[etree._Element] = []
    current: Optional[etree._Element] = None
    for p in list(paragraphs):
        txt = paragraph_text(p)
        starts = bool(MANUAL_NUM_RE.match(txt) or has_numpr(p) or get_pstyle(p) == "REFER")
        if current is None or starts:
            entries.append(p)
            current = p
            continue
        merged = (paragraph_text(current) + " " + txt).strip()
        replace_paragraph_text(current, merged)
        body.remove(p)
    return entries


def ensure_label_before_urls(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = MANUAL_NUM_RE.sub("", text)

    # Remove duplicated labels before processing.
    text = re.sub(r"\b(?:URL|DOI)\s*:\s*(?=(?:URL|DOI)\s*:)", "", text, flags=re.I)

    def repl(m: re.Match) -> str:
        url = m.group(0).rstrip(".,;")
        suffix = m.group(0)[len(url):]
        start = m.start()
        prefix_window = text[max(0, start - 12):start]
        is_doi = "doi.org/" in url.lower()
        if re.search(r"(?:URL|DOI)\s*:\s*$", prefix_window, re.I):
            # Existing label will be corrected in a second pass.
            return url + suffix
        return ("DOI: " if is_doi else "URL: ") + url + suffix

    text = URL_RE.sub(repl, text)
    text = re.sub(r"\bURL\s*:\s*(https?://(?:dx\.)?doi\.org/)", r"DOI: \1", text, flags=re.I)
    text = re.sub(r"\bDOI\s*:\s*(https?://(?![^\s]*doi\.org/))", r"URL: \1", text, flags=re.I)

    # Prefix bare DOI identifiers if not already labeled or inside a DOI URL.
    def doi_repl(m: re.Match) -> str:
        start = m.start()
        prefix = text[max(0, start - 8):start]
        if re.search(r"DOI\s*:\s*$", prefix, re.I) or "doi.org/" in prefix.lower():
            return m.group(0)
        return "DOI: " + m.group(0)

    text = BARE_DOI_RE.sub(doi_repl, text)
    text = re.sub(r"\b(URL|DOI)\s*:\s*\1\s*:\s*", lambda m: m.group(1).upper() + ": ", text, flags=re.I)
    return text.strip()


def patch_styles(target_styles: Path, template_styles: Path) -> None:
    tgt = read_xml(target_styles)
    src = read_xml(template_styles)
    troot = tgt.getroot(); sroot = src.getroot()
    for sid in CANONICAL_STYLE_IDS:
        sn = sroot.xpath(f'//w:style[@w:styleId="{sid}"]', namespaces=NS)
        if not sn:
            continue
        old = troot.xpath(f'//w:style[@w:styleId="{sid}"]', namespaces=NS)
        new = copy.deepcopy(sn[0])
        if old:
            idx = troot.index(old[0]); troot.remove(old[0]); troot.insert(idx, new)
        else:
            troot.append(new)
    write_xml(tgt, target_styles)


def patch_reference_abstract_numbering(target_num: Path, template_num: Path) -> None:
    tgt = read_xml(target_num); src = read_xml(template_num)
    troot = tgt.getroot(); sroot = src.getroot()
    src_abs = sroot.xpath('//w:abstractNum[@w:abstractNumId="2"]', namespaces=NS)
    if src_abs:
        old = troot.xpath('//w:abstractNum[@w:abstractNumId="2"]', namespaces=NS)
        new = copy.deepcopy(src_abs[0])
        if old:
            idx = troot.index(old[0]); troot.remove(old[0]); troot.insert(idx, new)
        else:
            # Abstract nums precede concrete nums.
            nums = troot.findall(qn("num"))
            idx = troot.index(nums[0]) if nums else len(troot)
            troot.insert(idx, new)
    write_xml(tgt, target_num)


def add_reference_num_instance(numbering_tree: etree._ElementTree) -> int:
    root = numbering_tree.getroot()
    ids = [int(n.get(qn("numId"))) for n in root.findall(qn("num")) if n.get(qn("numId"), "").isdigit()]
    num_id = max(ids or [0]) + 1
    num = etree.SubElement(root, qn("num")); num.set(qn("numId"), str(num_id))
    absid = etree.SubElement(num, qn("abstractNumId")); absid.set(qn("val"), "2")
    lvl = etree.SubElement(num, qn("lvlOverride")); lvl.set(qn("ilvl"), "0")
    start = etree.SubElement(lvl, qn("startOverride")); start.set(qn("val"), "1")
    return num_id


def set_reference_paragraph(p: etree._Element, text: str, num_id: int) -> None:
    text = ensure_label_before_urls(text)
    remove_all_content_except_ppr(p)
    ppr = get_ppr(p, True)
    for ch in list(ppr):
        ppr.remove(ch)
    ps = etree.SubElement(ppr, qn("pStyle")); ps.set(qn("val"), "REFER")
    numpr = etree.SubElement(ppr, qn("numPr"))
    il = etree.SubElement(numpr, qn("ilvl")); il.set(qn("val"), "0")
    ni = etree.SubElement(numpr, qn("numId")); ni.set(qn("val"), str(num_id))
    sp = etree.SubElement(ppr, qn("spacing")); sp.set(qn("before"), "0"); sp.set(qn("after"), "0"); sp.set(qn("line"), "240"); sp.set(qn("lineRule"), "auto")
    jc = etree.SubElement(ppr, qn("jc")); jc.set(qn("val"), "both")
    add_run(p, text, plain=True)


def normalize_table(table: etree._Element) -> None:
    for p in table.findall('.//w:p', NS):
        ppr = get_ppr(p, True)
        jc = ppr.find(qn("jc"))
        for ch in list(ppr):
            if ch.tag == qn("pStyle") or ch is jc:
                continue
            ppr.remove(ch)
        set_pstyle(p, "TABLETEXT")
        sp = etree.SubElement(ppr, qn("spacing")); sp.set(qn("before"), "0"); sp.set(qn("after"), "0"); sp.set(qn("line"), "240"); sp.set(qn("lineRule"), "auto")
        ind = etree.SubElement(ppr, qn("ind")); ind.set(qn("firstLine"), "0")
        for r in p.findall('.//w:r', NS):
            normalize_body_run(r)


def style_text_only_paragraph(p: etree._Element, style_id: str, *, plain: bool = False) -> None:
    txt = paragraph_text(p)
    ppr = get_ppr(p, True)
    pagebreak = ppr.find(qn("pageBreakBefore"))
    for ch in list(ppr):
        if ch is pagebreak:
            continue
        ppr.remove(ch)
    set_pstyle(p, style_id)
    remove_all_content_except_ppr(p)
    if txt:
        r = etree.SubElement(p, qn("r"))
        t = etree.SubElement(r, qn("t")); t.text = txt


def find_article_ranges(body: etree._Element) -> List[Tuple[etree._Element, int, int]]:
    blocks = list(body)
    starts = []
    for i, el in enumerate(blocks):
        if is_p(el) and paragraph_text(el) in SECTION_LABELS:
            starts.append(i)
    ranges = []
    for pos, start in enumerate(starts):
        if pos + 1 < len(starts):
            end = starts[pos + 1]
        else:
            end = len(blocks)
            # Protected tail begins with a new SCIENCE page after the reference block.
            for j in range(start + 1, len(blocks)):
                if is_p(blocks[j]) and paragraph_text(blocks[j]).startswith("SCIENCE"):
                    end = j
                    break
        ranges.append((blocks[start], start, end))
    return ranges


def article_blocks(body: etree._Element, section_el: etree._Element, next_section_el: Optional[etree._Element]) -> List[etree._Element]:
    blocks = list(body)
    start = blocks.index(section_el)
    if next_section_el is not None:
        end = blocks.index(next_section_el)
    else:
        end = len(blocks)
        for j in range(start + 1, len(blocks)):
            if is_p(blocks[j]) and paragraph_text(blocks[j]).startswith("SCIENCE"):
                end = j; break
    return blocks[start:end]


def normalize_article(body: etree._Element, section_el: etree._Element, next_section_el: Optional[etree._Element],
                      numbering_tree: etree._ElementTree) -> None:
    # Recompute dynamic block list after every structural edit when needed.
    blocks = article_blocks(body, section_el, next_section_el)
    style_text_only_paragraph(section_el, "SECTION")
    # Force article start on a new page while preserving exact SECTION style.
    ppr = get_ppr(section_el, True)
    if ppr.find(qn("pageBreakBefore")) is None:
        etree.SubElement(ppr, qn("pageBreakBefore"))

    # Find front-matter landmarks.
    title = next((p for p in blocks if is_p(p) and get_pstyle(p) == "11"), None)
    ref_title = next((p for p in blocks if is_p(p) and (get_pstyle(p) == "REF-TITLE" or REF_HEADING_RE.match(paragraph_text(p)))), None)
    if title is None:
        raise RuntimeError(f"Article title not found after section {paragraph_text(section_el)!r}")

    title_idx = blocks.index(title)
    front = blocks[:title_idx]

    # DOI/UDC styles and exact blank after the actual UDC line.
    udc_ps = []
    for p in front:
        if not is_p(p):
            continue
        txt = paragraph_text(p)
        if re.match(r"^(?:DOI\s*:|УДК\b|UDC\b)", txt, re.I):
            style_text_only_paragraph(p, "UDC")
            udc_ps.append(p)
    actual_udc = next((p for p in reversed(udc_ps) if re.match(r"^(?:УДК\b|UDC\b)", paragraph_text(p), re.I)), None)
    if actual_udc is not None:
        ensure_exactly_one_blank_after(body, actual_udc)
    else:
        raise RuntimeError(
            "UDC_LOOKUP_REQUIRED: collect title/annotation/keywords/section, perform online evidence-based UDC lookup, "
            "obtain operator approval, insert UDC, then rerun finalization"
        )

    # Contacts and author metadata.
    blocks = article_blocks(body, section_el, next_section_el)
    title_idx = blocks.index(title)
    for p in list(blocks[:title_idx]):
        if not is_p(p) or p is section_el or p in udc_ps or is_blank_p(p):
            continue
        txt = paragraph_text(p)
        cleaned_header = strip_contact_data(txt)
        if cleaned_header != txt:
            if not cleaned_header:
                body.remove(p)
                continue
            txt = cleaned_header
        sid = get_pstyle(p)
        if sid == "AUTOR":
            # Standalone name line: metadata belongs to following pip paragraphs, so service punctuation is removed.
            clean_name = re.sub(r"[,;:]\s*$", "", txt).strip()
            replace_paragraph_text(p, clean_name, style_id="AUTOR")
            clear_runs_to_style(p)
        elif sid == "pip" or txt:
            txt2 = normalize_role_case(txt)
            replace_paragraph_text(p, txt2, style_id="pip")
            # Let the exact pip style drive layout; clear direct run props.
            clear_runs_to_style(p)

    # Clean accidental multiple blanks in the front matter except mandated UDC gap.
    blocks = article_blocks(body, section_el, next_section_el)
    prev_blank = False
    for p in list(blocks[:blocks.index(title)]):
        if is_blank_p(p):
            if prev_blank:
                body.remove(p)
            prev_blank = True
        else:
            prev_blank = False

    style_text_only_paragraph(title, "11")
    ensure_exactly_one_blank_after(body, title)

    # Refresh article blocks after insertion/removal.
    blocks = article_blocks(body, section_el, next_section_el)
    # Empty service/spacing paragraphs inside articles always use Normal, never foreign No List styles.
    for blank in blocks:
        if is_blank_p(blank):
            ppr = get_ppr(blank, True)
            for ch in list(ppr):
                ppr.remove(ch)
            set_pstyle(blank, "a0")
    title_idx = blocks.index(title)
    ref_idx = blocks.index(ref_title) if ref_title in blocks else len(blocks)

    # Normalize article body paragraphs and semantic labels.
    for el in blocks[title_idx + 1:ref_idx]:
        if is_tbl(el):
            normalize_table(el)
            continue
        if not is_p(el) or is_blank_p(el):
            continue
        sid = get_pstyle(el)
        txt = paragraph_text(el)
        if sid == "ad":
            # Drawing paragraph: exact style, do not touch drawing XML.
            ppr = get_ppr(el, True)
            for ch in list(ppr): ppr.remove(ch)
            set_pstyle(el, "ad")
            continue
        if sid == "af6" or re.match(r"^(?:Рис\.|Figure\s+)\s*\d+", txt, re.I):
            style_text_only_paragraph(el, "af6")
            continue
        if canonicalize_annotation_or_keywords(el):
            continue
        if re.match(r"^(?:Таблиця|Table)\s*\d+\.?\s*$", txt, re.I):
            # Table number: right, bold, zero indent, keep with next.
            normalize_body_paragraph(el, zero_indent=True)
            ppr = get_ppr(el, True)
            jc = ppr.find(qn("jc"))
            if jc is None:
                jc = etree.SubElement(ppr, qn("jc"))
            jc.set(qn("val"), "right")
            etree.SubElement(ppr, qn("keepNext"))
            for r in el.findall('.//w:r', NS):
                rpr = r.find(qn("rPr"))
                if rpr is None: rpr = etree.SubElement(r, qn("rPr"))
                if rpr.find(qn("b")) is None: etree.SubElement(rpr, qn("b"))
            continue
        # Table title is the paragraph immediately before a table and after a table number.
        idx = blocks.index(el)
        if idx + 1 < len(blocks) and is_tbl(blocks[idx + 1]) and idx - 1 >= 0 and re.match(r"^(?:Таблиця|Table)\s*\d+", paragraph_text(blocks[idx - 1]), re.I):
            # A table title is a real caption-style paragraph, not Normal with look-alike formatting.
            style_text_only_paragraph(el, "af6")
            ppr = get_ppr(el, True)
            jc = ppr.find(qn("jc"))
            if jc is None:
                jc = etree.SubElement(ppr, qn("jc"))
            jc.set(qn("val"), "center")
            etree.SubElement(ppr, qn("keepNext"))
            for r in el.findall('.//w:r', NS):
                rpr = r.find(qn("rPr"))
                if rpr is None: rpr = etree.SubElement(r, qn("rPr"))
                if rpr.find(qn("b")) is None: etree.SubElement(rpr, qn("b"))
            continue
        if re.match(r"^(?:Джерело|Source)\s*:", txt, re.I):
            normalize_body_paragraph(el, zero_indent=True)
            for r in el.findall('.//w:r', NS):
                normalize_body_run(r)
                rpr = r.find(qn("rPr"))
                if rpr is None: rpr = etree.SubElement(r, qn("rPr"))
                if rpr.find(qn("i")) is None: etree.SubElement(rpr, qn("i"))
                if rpr.find(qn("iCs")) is None: etree.SubElement(rpr, qn("iCs"))
            continue
        normalize_body_paragraph(el, keep_num=True)

    # Spacing after figures/tables/sources.
    blocks = article_blocks(body, section_el, next_section_el)
    ref_idx = blocks.index(ref_title) if ref_title in blocks else len(blocks)
    for i, el in list(enumerate(blocks[:ref_idx])):
        if is_p(el):
            txt = paragraph_text(el)
            sid = get_pstyle(el)
            if re.match(r"^(?:Джерело|Source)\s*:", txt, re.I):
                ensure_exactly_one_blank_after(body, el)
            elif sid == "af6":
                # If a source line follows (possibly after blanks), source owns the gap.
                fresh = list(body); pos = fresh.index(el); j = pos + 1
                while j < len(fresh) and is_blank_p(fresh[j]): j += 1
                if j >= len(fresh) or not (is_p(fresh[j]) and re.match(r"^(?:Джерело|Source)\s*:", paragraph_text(fresh[j]), re.I)):
                    ensure_exactly_one_blank_after(body, el)
        elif is_tbl(el):
            fresh = list(body); pos = fresh.index(el); j = pos + 1
            while j < len(fresh) and is_blank_p(fresh[j]): j += 1
            if j < len(fresh) and is_p(fresh[j]) and re.match(r"^(?:Джерело|Source)\s*:", paragraph_text(fresh[j]), re.I):
                # Remove blanks between table and its source.
                while pos + 1 < len(body) and is_blank_p(body[pos + 1]): body.remove(body[pos + 1])
            else:
                ensure_exactly_one_blank_after(body, el)

    # References heading and entries.
    if ref_title is not None:
        replace_paragraph_text(ref_title, "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:", style_id="REF-TITLE")
        clear_runs_to_style(ref_title)
        ensure_exactly_one_blank_before(body, ref_title)
        ensure_exactly_one_blank_after(body, ref_title)
        blocks = article_blocks(body, section_el, next_section_el)
        ref_idx = blocks.index(ref_title)
        refs = reconstruct_reference_entries(body, blocks[ref_idx + 1:])
        num_id = add_reference_num_instance(numbering_tree)
        for p in refs:
            set_reference_paragraph(p, paragraph_text(p), num_id)


def process(input_docx: Path, template_dotx: Path, output_docx: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="naukainfo_finalize_") as td:
        work = Path(td) / "doc"
        template = Path(td) / "template"
        work.mkdir(); template.mkdir()
        with zipfile.ZipFile(input_docx) as z: z.extractall(work)
        with zipfile.ZipFile(template_dotx) as z: z.extractall(template)

        patch_styles(work / "word/styles.xml", template / "word/styles.xml")
        patch_reference_abstract_numbering(work / "word/numbering.xml", template / "word/numbering.xml")

        doc_tree = read_xml(work / "word/document.xml")
        num_tree = read_xml(work / "word/numbering.xml")
        body = doc_tree.getroot().find("w:body", NS)
        sections = [el for el in list(body) if is_p(el) and get_pstyle(el) == "SECTION" and paragraph_text(el) in SECTION_LABELS]
        for i, sec in enumerate(sections):
            normalize_article(body, sec, sections[i + 1] if i + 1 < len(sections) else None, num_tree)

        # The protected final service page must start on a fresh page, never at the foot of the last references page.
        after_articles = False
        for el in list(body):
            if sections and el is sections[-1]:
                after_articles = True
            if after_articles and is_p(el) and paragraph_text(el).startswith("SCIENCE") and get_pstyle(el) != "SECTION":
                ppr = get_ppr(el, True)
                if ppr.find(qn("pageBreakBefore")) is None:
                    etree.SubElement(ppr, qn("pageBreakBefore"))
                break

        write_xml(doc_tree, work / "word/document.xml")
        write_xml(num_tree, work / "word/numbering.xml")

        output_docx.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(work.rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(work).as_posix())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_docx", type=Path)
    ap.add_argument("template_dotx", type=Path)
    ap.add_argument("output_docx", type=Path)
    args = ap.parse_args()
    process(args.input_docx, args.template_dotx, args.output_docx)


if __name__ == "__main__":
    main()
