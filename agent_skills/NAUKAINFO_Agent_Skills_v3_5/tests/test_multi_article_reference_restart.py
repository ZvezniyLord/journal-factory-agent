import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lxml import etree
from scripts.multi_article_reference_restart import NS, q, restart_reference_blocks


def p(style, text=""):
    el = etree.Element(q("p"))
    ppr = etree.SubElement(el, q("pPr"))
    ps = etree.SubElement(ppr, q("pStyle")); ps.set(q("val"), style)
    if text:
        r = etree.SubElement(el, q("r")); t = etree.SubElement(r, q("t")); t.text = text
    return el


def test_each_article_reference_block_gets_distinct_restart_at_one():
    doc = etree.Element(q("document")); body = etree.SubElement(doc, q("body"))
    body.extend([p("REF-TITLE", "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:"), p("REFER", "A"), p("REFER", "B"),
                 p("SECTION", "NEXT"), p("REF-TITLE", "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:"), p("REFER", "C")])
    numbering = etree.Element(q("numbering"))
    audit = restart_reference_blocks(doc, numbering)
    assert [x["entries"] for x in audit] == [2, 1]
    assert audit[0]["num_id"] != audit[1]["num_id"]
    for item in audit:
        num = numbering.xpath(f'./w:num[@w:numId="{item["num_id"]}"]', namespaces=NS)[0]
        assert num.find('./w:lvlOverride/w:startOverride', NS).get(q('val')) == '1'
