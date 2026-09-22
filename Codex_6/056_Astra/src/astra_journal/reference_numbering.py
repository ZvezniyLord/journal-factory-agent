from __future__ import annotations

from dataclasses import dataclass

from docx.oxml import OxmlElement
from docx.oxml.ns import qn


@dataclass
class ReferenceNumberingPlan:
    abstract_num_id: int
    next_num_id: int
    article_count: int = 0


def ensure_shared_reference_abstract_num(
    doc,
    *,
    abstract_num_id: int = 7000,
) -> ReferenceNumberingPlan:
    numbering = doc.part.numbering_part.element

    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_num_id))

    multi = OxmlElement("w:multiLevelType")
    multi.set(qn("w:val"), "singleLevel")
    abstract.append(multi)

    lvl = OxmlElement("w:lvl")
    lvl.set(qn("w:ilvl"), "0")

    start = OxmlElement("w:start")
    start.set(qn("w:val"), "1")

    num_fmt = OxmlElement("w:numFmt")
    num_fmt.set(qn("w:val"), "decimal")

    lvl_text = OxmlElement("w:lvlText")
    lvl_text.set(qn("w:val"), "%1.")

    suff = OxmlElement("w:suff")
    suff.set(qn("w:val"), "tab")

    ppr = OxmlElement("w:pPr")
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "num")
    tab.set(qn("w:pos"), "720")
    tabs.append(tab)

    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "720")
    ind.set(qn("w:hanging"), "360")

    ppr.extend([tabs, ind])
    lvl.extend([start, num_fmt, lvl_text, suff, ppr])
    abstract.append(lvl)
    numbering.append(abstract)

    return ReferenceNumberingPlan(
        abstract_num_id=abstract_num_id,
        next_num_id=abstract_num_id + 1,
    )


def create_article_reference_num(doc, plan: ReferenceNumberingPlan) -> int:
    numbering = doc.part.numbering_part.element
    num_id = plan.next_num_id
    plan.next_num_id += 1

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))

    abstract_ref = OxmlElement("w:abstractNumId")
    abstract_ref.set(qn("w:val"), str(plan.abstract_num_id))
    num.append(abstract_ref)

    # Word-stable strategy B:
    # first logical list uses the shared abstract start=1.
    # each later logical list gets an explicit startOverride=1.
    if plan.article_count > 0:
        override = OxmlElement("w:lvlOverride")
        override.set(qn("w:ilvl"), "0")
        start_override = OxmlElement("w:startOverride")
        start_override.set(qn("w:val"), "1")
        override.append(start_override)
        num.append(override)

    numbering.append(num)
    plan.article_count += 1
    return num_id


def bind_reference_numbering(paragraph, num_id: int) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    numpr = ppr.find(qn("w:numPr"))
    if numpr is None:
        numpr = OxmlElement("w:numPr")
        ppr.append(numpr)
    else:
        for child in list(numpr):
            numpr.remove(child)

    ilvl = OxmlElement("w:ilvl")
    ilvl.set(qn("w:val"), "0")
    num = OxmlElement("w:numId")
    num.set(qn("w:val"), str(num_id))
    numpr.extend([ilvl, num])
