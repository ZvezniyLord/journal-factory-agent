from __future__ import annotations

from pathlib import Path
import json
import re
import zipfile
from xml.etree import ElementTree as ET

from .archive_workspace import sha256_file


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "v": "urn:schemas-microsoft-com:vml",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def create_source_snapshot(source_file: Path, article_id: str, snapshots_root: Path, workspace_source: Path) -> dict:
    out_dir = snapshots_root / article_id
    out_dir.mkdir(parents=True, exist_ok=True)
    if source_file.suffix.lower() == ".docx":
        snapshot = snapshot_docx(source_file, workspace_source)
    elif source_file.suffix.lower() == ".doc":
        snapshot = snapshot_legacy_doc(source_file, workspace_source)
    else:
        raise ValueError(f"Unsupported article source extension: {source_file.suffix}")
    (out_dir / "source_snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return snapshot


def snapshot_docx(path: Path, workspace_source: Path) -> dict:
    blockers: list[str] = []
    warnings: list[str] = []
    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        document_xml = _read_xml(package, "word/document.xml")
        rels_xml = _read_xml(package, "word/_rels/document.xml.rels", required=False)
        numbering_xml = _read_text(package, "word/numbering.xml", required=False)
        styles_xml = _read_text(package, "word/styles.xml", required=False)
        media_hashes = {
            name: _sha256_bytes(package.read(name))
            for name in sorted(names)
            if name.startswith("word/media/") and not name.endswith("/")
        }
        paragraphs = _extract_paragraphs(document_xml)
        tables = _extract_tables(document_xml)
        textboxes = _extract_textboxes(document_xml)
        relationships = _extract_relationships(rels_xml) if rels_xml is not None else []
        unsupported = _unsupported_parts(names)
        if unsupported:
            blockers.append("unsupported_ooxml_parts")
        object_risk = "blocked" if blockers else "none"
        visible_text_parts = [item["text"] for item in paragraphs if item["text"]]
        visible_text_parts.extend(cell["text"] for table in tables for cell in table["table_cells"] if cell["text"])
        visible_text_parts.extend(item["text"] for item in textboxes if item["text"])
        return {
            "source_path": path.relative_to(workspace_source).as_posix(),
            "source_sha256": sha256_file(path),
            "visible_text": "\n".join(visible_text_parts),
            "paragraphs": paragraphs,
            "runs": [run for paragraph in paragraphs for run in paragraph["runs"]],
            "paragraph_order": [paragraph["index"] for paragraph in paragraphs],
            "tables": tables,
            "table_cells": [cell for table in tables for cell in table["table_cells"]],
            "merge_map": _extract_merge_map(document_xml),
            "numbering": {
                "present": numbering_xml is not None,
                "sha256": _sha256_text(numbering_xml) if numbering_xml is not None else None,
            },
            "styles": {
                "present": styles_xml is not None,
                "sha256": _sha256_text(styles_xml) if styles_xml is not None else None,
            },
            "images": sorted(media_hashes),
            "media_hashes": media_hashes,
            "relationships": relationships,
            "drawings": _count_elements(document_xml, ".//w:drawing"),
            "shapes": _count_elements(document_xml, ".//v:shape"),
            "textboxes": textboxes,
            "charts": sorted(name for name in names if name.startswith("word/charts/")),
            "equations": _count_elements(document_xml, ".//m:oMath"),
            "OLE": sorted(name for name in names if name.startswith("word/embeddings/")),
            "section_breaks": _count_elements(document_xml, ".//w:sectPr"),
            "page_breaks": len(document_xml.findall(".//w:br[@w:type='page']", NS)),
            "object_risk": object_risk,
            "unsupported_parts": unsupported,
            "warnings": warnings,
            "blockers": blockers,
            "snapshot_status": "BLOCKED" if blockers else "PASS",
        }


def snapshot_legacy_doc(path: Path, workspace_source: Path) -> dict:
    return {
        "source_path": path.relative_to(workspace_source).as_posix(),
        "source_sha256": sha256_file(path),
        "visible_text": "",
        "paragraphs": [],
        "runs": [],
        "paragraph_order": [],
        "tables": [],
        "table_cells": [],
        "merge_map": [],
        "numbering": {"present": False, "sha256": None},
        "images": [],
        "media_hashes": {},
        "relationships": [],
        "drawings": 0,
        "shapes": 0,
        "textboxes": [],
        "charts": [],
        "equations": 0,
        "OLE": [],
        "section_breaks": 0,
        "page_breaks": 0,
        "object_risk": "unverified",
        "unsupported_parts": [],
        "conversion_method": None,
        "converted_sha256": None,
        "blockers": ["legacy_doc_conversion_not_available"],
        "warnings": [],
        "snapshot_status": "BLOCKED",
    }


def extract_docx_evidence_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as package:
            root = _read_xml(package, "word/document.xml")
        paragraphs = _extract_paragraphs(root)
        tables = _extract_tables(root)
        textboxes = _extract_textboxes(root)
        values = [item["text"] for item in paragraphs]
        values.extend(cell["text"] for table in tables for cell in table["table_cells"])
        values.extend(item["text"] for item in textboxes)
        return "\n".join(item for item in values if item)
    except Exception:  # noqa: BLE001
        return ""


def _extract_paragraphs(root: ET.Element) -> list[dict]:
    paragraphs = []
    for index, paragraph in enumerate(root.findall(".//w:body/w:p", NS)):
        runs = []
        for run_index, run in enumerate(paragraph.findall(".//w:r", NS)):
            text = "".join(node.text or "" for node in run.findall(".//w:t", NS))
            if text:
                runs.append({"paragraph_index": index, "run_index": run_index, "text": text})
        para_text = "".join(run["text"] for run in runs)
        paragraphs.append({"index": index, "text": para_text, "runs": runs})
    return paragraphs


def _extract_tables(root: ET.Element) -> list[dict]:
    tables = []
    for table_index, table in enumerate(root.findall(".//w:tbl", NS)):
        cells = []
        for row_index, row in enumerate(table.findall("./w:tr", NS)):
            for cell_index, cell in enumerate(row.findall("./w:tc", NS)):
                text = "".join(node.text or "" for node in cell.findall(".//w:t", NS))
                cells.append({"table": table_index, "row": row_index, "cell": cell_index, "text": text})
        tables.append({"table_index": table_index, "table_cells": cells})
    return tables


def _extract_textboxes(root: ET.Element) -> list[dict]:
    boxes = []
    for index, box in enumerate(root.findall(".//w:txbxContent", NS)):
        text = "".join(node.text or "" for node in box.findall(".//w:t", NS))
        boxes.append({"index": index, "text": text})
    return boxes


def _extract_merge_map(root: ET.Element) -> list[dict]:
    merges = []
    for table_index, table in enumerate(root.findall(".//w:tbl", NS)):
        for row_index, row in enumerate(table.findall("./w:tr", NS)):
            for cell_index, cell in enumerate(row.findall("./w:tc", NS)):
                grid_span = cell.find(".//w:gridSpan", NS)
                v_merge = cell.find(".//w:vMerge", NS)
                if grid_span is not None or v_merge is not None:
                    merges.append(
                        {
                            "table": table_index,
                            "row": row_index,
                            "cell": cell_index,
                            "grid_span": grid_span.get(f"{{{NS['w']}}}val") if grid_span is not None else None,
                            "v_merge": v_merge.get(f"{{{NS['w']}}}val") if v_merge is not None else None,
                        }
                    )
    return merges


def _extract_relationships(root: ET.Element) -> list[dict]:
    result = []
    for rel in root.findall(".//rel:Relationship", NS):
        result.append({"id": rel.get("Id"), "type": rel.get("Type"), "target": rel.get("Target")})
    return result


def _unsupported_parts(names: set[str]) -> list[str]:
    unsupported = []
    for name in sorted(names):
        if re.search(r"activeX|vbaProject", name, flags=re.I):
            unsupported.append(name)
    return unsupported


def _read_xml(package: zipfile.ZipFile, name: str, required: bool = True) -> ET.Element | None:
    try:
        return ET.fromstring(package.read(name))
    except KeyError:
        if required:
            raise
        return None


def _read_text(package: zipfile.ZipFile, name: str, required: bool = True) -> str | None:
    try:
        return package.read(name).decode("utf-8", errors="replace")
    except KeyError:
        if required:
            raise
        return None


def _count_elements(root: ET.Element, pattern: str) -> int:
    return len(root.findall(pattern, NS))


def _sha256_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))
