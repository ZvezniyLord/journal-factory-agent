from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import tempfile
import zipfile

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
STYLE_ID = f"{{{W_NS}}}styleId"
REQUIRED_STYLE_IDS = ("AUTOR", "SECTION", "Назва1")


def merge_template_styles(etalon: Path, template: Path, output: Path, report_path: Path | None = None) -> dict:
    """Copy missing paragraph/character/table styles from DOTX into ETALON.

    Existing ETALON style ids remain authoritative. Missing style definitions are
    copied without modifying either input package.
    """
    if not etalon.is_file():
        raise FileNotFoundError(etalon)
    if not template.is_file():
        raise FileNotFoundError(template)

    with zipfile.ZipFile(etalon) as package:
        target_parts = {name: package.read(name) for name in package.namelist()}
    with zipfile.ZipFile(template) as package:
        source_styles = package.read("word/styles.xml")

    if "word/styles.xml" not in target_parts:
        raise ValueError("ETALON has no word/styles.xml")

    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    target_root = etree.fromstring(target_parts["word/styles.xml"], parser)
    source_root = etree.fromstring(source_styles, parser)

    existing = {
        value
        for style in target_root.xpath("./w:style", namespaces=NS)
        if (value := style.get(STYLE_ID))
    }
    added: list[str] = []
    collisions: list[str] = []

    for style in source_root.xpath("./w:style", namespaces=NS):
        style_id = style.get(STYLE_ID)
        if not style_id:
            continue
        if style_id in existing:
            collisions.append(style_id)
            continue
        target_root.append(deepcopy(style))
        existing.add(style_id)
        added.append(style_id)

    target_parts["word/styles.xml"] = etree.tostring(
        target_root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False, dir=output.parent) as handle:
        temp_path = Path(handle.name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
            for name, payload in target_parts.items():
                package.writestr(name, payload)
        temp_path.replace(output)
    finally:
        temp_path.unlink(missing_ok=True)

    missing_required = [style_id for style_id in REQUIRED_STYLE_IDS if style_id not in existing]
    report = {
        "etalon": str(etalon),
        "template": str(template),
        "output": str(output),
        "added_style_ids": sorted(added),
        "existing_style_collisions": sorted(collisions),
        "required_style_ids": list(REQUIRED_STYLE_IDS),
        "missing_required_style_ids": missing_required,
        "status": "PASS" if not missing_required else "BLOCKED",
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
