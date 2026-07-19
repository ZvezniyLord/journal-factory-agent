from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import tempfile
import zipfile

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W_VAL = f"{{{W_NS}}}val"


def load_typography_profile(profiles_path: Path, profile_name: str) -> dict[str, Any]:
    payload = json.loads(profiles_path.read_text(encoding="utf-8"))
    profiles = payload.get("profiles", {})
    if profile_name not in profiles:
        raise ValueError(f"Unknown typography profile: {profile_name}")
    profile = dict(profiles[profile_name])
    size = profile.get("body_font_size_pt")
    if not isinstance(size, (int, float)) or not 6 <= float(size) <= 36:
        raise ValueError(f"Invalid body_font_size_pt for {profile_name}: {size}")
    profile["name"] = profile_name
    return profile


def apply_typography_profile(
    input_docx: Path,
    output_docx: Path,
    profiles_path: Path,
    profile_name: str,
    report_path: Path | None = None,
) -> dict[str, Any]:
    """Set document defaults and the default body paragraph style.

    Explicit sizes of headings, captions, UDC, DOI and other specialized styles
    are preserved. Article-level direct formatting is audited and normalized by
    the article-preparation phase, not silently removed here.
    """
    profile = load_typography_profile(profiles_path, profile_name)
    half_points = str(int(round(float(profile["body_font_size_pt"]) * 2)))

    with zipfile.ZipFile(input_docx) as package:
        parts = {name: package.read(name) for name in package.namelist()}
    if "word/styles.xml" not in parts:
        raise ValueError("DOCX has no word/styles.xml")

    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    root = etree.fromstring(parts["word/styles.xml"], parser)

    defaults_rpr = _ensure_path(root, ["docDefaults", "rPrDefault", "rPr"])
    _set_size(defaults_rpr, half_points)

    default_styles = root.xpath(
        "./w:style[@w:type='paragraph' and @w:default='1']",
        namespaces=NS,
    )
    if not default_styles:
        default_styles = [
            style
            for style in root.xpath("./w:style[@w:type='paragraph']", namespaces=NS)
            if _style_name(style) == "Normal"
        ]
    if not default_styles:
        raise ValueError("Default paragraph style was not found")

    default_style = default_styles[0]
    rpr = default_style.find("w:rPr", namespaces=NS)
    if rpr is None:
        rpr = etree.SubElement(default_style, f"{{{W_NS}}}rPr")
    _set_size(rpr, half_points)

    parts["word/styles.xml"] = etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )

    output_docx.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False, dir=output_docx.parent) as handle:
        temp_path = Path(handle.name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for name, content in parts.items():
                package.writestr(name, content)
        temp_path.replace(output_docx)
    finally:
        temp_path.unlink(missing_ok=True)

    report = {
        "status": "PASS",
        "profile": profile_name,
        "body_font_size_pt": profile["body_font_size_pt"],
        "half_points": int(half_points),
        "input": str(input_docx),
        "output": str(output_docx),
        "default_style_id": default_style.get(f"{{{W_NS}}}styleId"),
        "default_style_name": _style_name(default_style),
        "preserved_specialized_style_sizes": True,
        "direct_run_size_normalization_deferred_to_article_preparation": True,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _ensure_path(root: etree._Element, names: list[str]) -> etree._Element:
    current = root
    for name in names:
        child = current.find(f"w:{name}", namespaces=NS)
        if child is None:
            child = etree.SubElement(current, f"{{{W_NS}}}{name}")
        current = child
    return current


def _set_size(rpr: etree._Element, half_points: str) -> None:
    for element_name in ("sz", "szCs"):
        element = rpr.find(f"w:{element_name}", namespaces=NS)
        if element is None:
            element = etree.SubElement(rpr, f"{{{W_NS}}}{element_name}")
        element.set(W_VAL, half_points)


def _style_name(style: etree._Element) -> str:
    name = style.find("w:name", namespaces=NS)
    return str(name.get(W_VAL)) if name is not None and name.get(W_VAL) else ""
