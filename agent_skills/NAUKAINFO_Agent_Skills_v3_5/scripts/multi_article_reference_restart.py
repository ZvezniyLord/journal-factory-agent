from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def q(tag: str) -> str:
    return f"{{{W}}}{tag}"


def _style(p):
    el = p.find("./w:pPr/w:pStyle", NS)
    return el.get(q("val")) if el is not None else None


def _ensure_ppr(p):
    ppr = p.find("w:pPr", NS)
    if ppr is None:
        ppr = etree.Element(q("pPr"))
        p.insert(0, ppr)
    return ppr


def _remove(ppr, names):
    for name in names:
        for el in ppr.findall(f"w:{name}", NS):
            ppr.remove(el)


def _next_num_id(numbering_root) -> int:
    ids = [int(n.get(q("numId"))) for n in numbering_root.findall("w:num", NS)
           if (n.get(q("numId")) or "").isdigit()]
    return max(ids or [0]) + 1


def _make_num(numbering_root, abstract_num_id: str = "1") -> str:
    num_id = str(_next_num_id(numbering_root))
    num = etree.Element(q("num")); num.set(q("numId"), num_id)
    abs_id = etree.Element(q("abstractNumId")); abs_id.set(q("val"), abstract_num_id)
    override = etree.Element(q("lvlOverride")); override.set(q("ilvl"), "0")
    start = etree.Element(q("startOverride")); start.set(q("val"), "1")
    override.append(start); num.append(abs_id); num.append(override); numbering_root.append(num)
    return num_id


def _apply_num(p, num_id: str) -> None:
    ppr = _ensure_ppr(p)
    _remove(ppr, ["numPr", "tabs", "ind"])
    num_pr = etree.Element(q("numPr"))
    ilvl = etree.Element(q("ilvl")); ilvl.set(q("val"), "0")
    nid = etree.Element(q("numId")); nid.set(q("val"), num_id)
    num_pr.append(ilvl); num_pr.append(nid)
    style_el = ppr.find("w:pStyle", NS)
    ppr.insert(ppr.index(style_el) + 1 if style_el is not None else 0, num_pr)


def restart_reference_blocks(document_root, numbering_root) -> list[dict]:
    """Assign a fresh numbering instance starting at 1 to every contiguous REFER block."""
    body = document_root.find("w:body", NS)
    children = list(body)
    audit = []
    for i, el in enumerate(children):
        if el.tag != q("p") or _style(el) != "REF-TITLE":
            continue
        j = i + 1
        while j < len(children) and children[j].tag == q("p") and not children[j].xpath(".//w:t", namespaces=NS):
            j += 1
        refs = []
        while j < len(children) and children[j].tag == q("p") and _style(children[j]) == "REFER":
            refs.append(children[j]); j += 1
        num_id = _make_num(numbering_root)
        for p in refs:
            _apply_num(p, num_id)
        audit.append({"num_id": num_id, "entries": len(refs), "start": 1})
    return audit


def patch_docx(src: str | Path, dst: str | Path) -> list[dict]:
    src, dst = Path(src), Path(dst)
    with ZipFile(src, "r") as zin:
        document_root = etree.fromstring(zin.read("word/document.xml"))
        numbering_root = etree.fromstring(zin.read("word/numbering.xml"))
        audit = restart_reference_blocks(document_root, numbering_root)
        with ZipFile(dst, "w", ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    data = etree.tostring(document_root, xml_declaration=True, encoding="UTF-8", standalone="yes")
                elif item.filename == "word/numbering.xml":
                    data = etree.tostring(numbering_root, xml_declaration=True, encoding="UTF-8", standalone="yes")
                else:
                    data = zin.read(item.filename)
                zout.writestr(item, data)
    return audit


if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    args = ap.parse_args()
    print(json.dumps(patch_docx(args.src, args.dst), ensure_ascii=False, indent=2))
