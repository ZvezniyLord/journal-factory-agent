from __future__ import annotations

from pathlib import Path
import json
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from docx import Document


def style_snapshot(template_path: Path) -> dict:
    try:
        doc = Document(str(template_path))
        styles = []
        for style in doc.styles:
            font = getattr(style, "font", None)
            styles.append({
                "name": style.name,
                "type": str(style.type),
                "font_name": font.name if font else None,
                "font_size_pt": round(font.size.pt, 2) if font and font.size else None,
                "bold": font.bold if font else None,
                "italic": font.italic if font else None,
            })
    except ValueError:
        styles = _snapshot_dotx_styles(template_path)
    return {"template": str(template_path), "styles": styles}


def write_style_snapshot(snapshot: dict, path: Path) -> Path:
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _snapshot_dotx_styles(template_path: Path) -> list[dict]:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(template_path) as zf:
        root = ET.fromstring(zf.read("word/styles.xml"))
    styles: list[dict] = []
    for style in root.findall("w:style", ns):
        name = style.find("w:name", ns)
        rpr = style.find("w:rPr", ns)
        size = rpr.find("w:sz", ns) if rpr is not None else None
        fonts = rpr.find("w:rFonts", ns) if rpr is not None else None
        styles.append({
            "name": name.attrib.get(f"{{{ns['w']}}}val") if name is not None else style.attrib.get(f"{{{ns['w']}}}styleId"),
            "type": style.attrib.get(f"{{{ns['w']}}}type"),
            "font_name": fonts.attrib.get(f"{{{ns['w']}}}ascii") if fonts is not None else None,
            "font_size_pt": int(size.attrib[f"{{{ns['w']}}}val"]) / 2 if size is not None and f"{{{ns['w']}}}val" in size.attrib else None,
            "bold": rpr.find("w:b", ns) is not None if rpr is not None else None,
            "italic": rpr.find("w:i", ns) is not None if rpr is not None else None,
        })
    return styles
