from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from lxml import etree

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W = f"{{{W_NS}}}"


@dataclass(frozen=True)
class StyleFinding:
    style_id: str
    style_name: str
    issue: str


def _style_name(style: etree._Element) -> str:
    node = style.find("w:name", NS)
    return node.get(W + "val", "") if node is not None else ""


def inspect_styles_xml(data: bytes) -> dict[str, Any]:
    root = etree.fromstring(data)
    auto_redefine: list[dict[str, str]] = []
    theme_font_dependencies: list[dict[str, str]] = []
    normal: dict[str, Any] = {}

    for style in root.findall("w:style", NS):
        style_id = style.get(W + "styleId", "")
        name = _style_name(style)
        if style.find("w:autoRedefine", NS) is not None:
            auto_redefine.append({"style_id": style_id, "name": name})

        rfonts = style.find("w:rPr/w:rFonts", NS)
        if rfonts is not None:
            themed = {
                key: rfonts.get(W + key)
                for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")
                if rfonts.get(W + key)
            }
            if themed:
                theme_font_dependencies.append(
                    {
                        "style_id": style_id,
                        "name": name,
                        "theme_refs": themed,
                    }
                )

        if style_id == "Normal":
            ppr = style.find("w:pPr", NS)
            rpr = style.find("w:rPr", NS)
            jc = ppr.find("w:jc", NS) if ppr is not None else None
            spacing = ppr.find("w:spacing", NS) if ppr is not None else None
            sz = rpr.find("w:sz", NS) if rpr is not None else None
            fonts = rpr.find("w:rFonts", NS) if rpr is not None else None
            normal = {
                "alignment": jc.get(W + "val") if jc is not None else None,
                "after": spacing.get(W + "after") if spacing is not None else None,
                "line": spacing.get(W + "line") if spacing is not None else None,
                "size_half_points": sz.get(W + "val") if sz is not None else None,
                "fonts": {
                    key: fonts.get(W + key)
                    for key in ("ascii", "hAnsi", "eastAsia", "cs", "asciiTheme", "hAnsiTheme")
                    if fonts is not None and fonts.get(W + key)
                },
            }

    return {
        "auto_redefine": auto_redefine,
        "theme_font_dependencies": theme_font_dependencies,
        "normal": normal,
    }


def inspect_theme_xml(data: bytes) -> dict[str, Any]:
    root = etree.fromstring(data)
    a_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
    ns = {"a": a_ns}

    def typeface(path: str) -> str | None:
        node = root.find(path, ns)
        return node.get("typeface") if node is not None else None

    return {
        "major_latin": typeface(".//a:themeElements/a:fontScheme/a:majorFont/a:latin"),
        "minor_latin": typeface(".//a:themeElements/a:fontScheme/a:minorFont/a:latin"),
    }


def inspect_document_sections(data: bytes) -> dict[str, Any]:
    root = etree.fromstring(data)
    values: list[int | None] = []
    for sect in root.findall(".//w:sectPr", NS):
        pgmar = sect.find("w:pgMar", NS)
        raw = pgmar.get(W + "footer") if pgmar is not None else None
        values.append(int(raw) if raw and raw.isdigit() else None)
    return {
        "section_count": len(values),
        "footer_twips": values,
        "footer_distance_consistent": len({v for v in values if v is not None}) <= 1,
    }


def inspect_docx(path: str | Path) -> dict[str, Any]:
    docx = Path(path)
    with ZipFile(docx) as zf:
        names = set(zf.namelist())
        report: dict[str, Any] = {
            "path": str(docx),
            "styles": inspect_styles_xml(zf.read("word/styles.xml"))
            if "word/styles.xml" in names
            else None,
            "theme": inspect_theme_xml(zf.read("word/theme/theme1.xml"))
            if "word/theme/theme1.xml" in names
            else None,
            "sections": inspect_document_sections(zf.read("word/document.xml"))
            if "word/document.xml" in names
            else None,
        }
    return report


def harden_styles_xml(
    data: bytes,
    *,
    style_ids: set[str],
    font_name: str = "Times New Roman",
    size_pt: float | None = None,
    alignment: str | None = None,
    line_twips: int | None = None,
    after_twips: int | None = None,
    first_line_twips: int | None = None,
) -> bytes:
    root = etree.fromstring(data)

    for style in root.findall("w:style", NS):
        style_id = style.get(W + "styleId", "")
        if style_id not in style_ids:
            continue
        if style_id == "Normal":
            raise ValueError("Global Normal mutation is forbidden")

        for node in style.findall("w:autoRedefine", NS):
            node.getparent().remove(node)

        rpr = style.find("w:rPr", NS)
        if rpr is None:
            rpr = etree.SubElement(style, W + "rPr")
        rfonts = rpr.find("w:rFonts", NS)
        if rfonts is None:
            rfonts = etree.SubElement(rpr, W + "rFonts")
        for key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
            rfonts.attrib.pop(W + key, None)
        for key in ("ascii", "hAnsi", "eastAsia", "cs"):
            rfonts.set(W + key, font_name)

        if size_pt is not None:
            val = str(int(round(size_pt * 2)))
            for key in ("sz", "szCs"):
                node = rpr.find(f"w:{key}", NS)
                if node is None:
                    node = etree.SubElement(rpr, W + key)
                node.set(W + "val", val)

        ppr = style.find("w:pPr", NS)
        if ppr is None:
            ppr = etree.SubElement(style, W + "pPr")

        if alignment is not None:
            jc = ppr.find("w:jc", NS)
            if jc is None:
                jc = etree.SubElement(ppr, W + "jc")
            jc.set(W + "val", alignment)

        if any(v is not None for v in (line_twips, after_twips)):
            spacing = ppr.find("w:spacing", NS)
            if spacing is None:
                spacing = etree.SubElement(ppr, W + "spacing")
            if line_twips is not None:
                spacing.set(W + "line", str(line_twips))
                spacing.set(W + "lineRule", "auto")
            if after_twips is not None:
                spacing.set(W + "after", str(after_twips))

        if first_line_twips is not None:
            ind = ppr.find("w:ind", NS)
            if ind is None:
                ind = etree.SubElement(ppr, W + "ind")
            ind.set(W + "firstLine", str(first_line_twips))

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone="yes",
    )


def write_report(path: str | Path, report: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
