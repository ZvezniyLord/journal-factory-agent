from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import json
import re
import tempfile
import zipfile

from lxml import etree

from .archive_workspace import sha256_file
from .conference_metadata import format_metadata_value


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W_NS}
W_VAL = f"{{{W_NS}}}val"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def materialize_service_pages(
    input_docx: Path,
    output_docx: Path,
    metadata: dict[str, Any],
    report_path: Path | None = None,
) -> dict[str, Any]:
    replacements = [
        {
            "source": str(item["source"]),
            "target": format_metadata_value(str(item["target"]), metadata),
            "preserve_case": bool(item.get("preserve_case", False)),
        }
        for item in metadata["template_replacements"]
    ]
    with zipfile.ZipFile(input_docx) as package:
        parts = {name: package.read(name) for name in package.namelist()}

    replacement_counts: dict[str, int] = {item["source"]: 0 for item in replacements}
    dynamic_counts: dict[str, int] = {}
    layout_counts: dict[str, int] = {}
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    for name, payload in list(parts.items()):
        if not name.endswith((".xml", ".rels")):
            continue
        try:
            root = etree.fromstring(payload, parser)
        except etree.XMLSyntaxError:
            continue
        changed = False
        if root.tag == f"{{{R_NS}}}Relationships":
            for relationship in root:
                target = relationship.get("Target")
                if not target:
                    continue
                updated, counts = _replace_value(target, replacements)
                if updated != target:
                    relationship.set("Target", updated)
                    changed = True
                    _merge_counts(replacement_counts, counts)
        else:
            for paragraph in root.xpath(".//w:p", namespaces=NS):
                counts = _replace_paragraph_text(paragraph, replacements)
                if any(counts.values()):
                    changed = True
                    _merge_counts(replacement_counts, counts)
            for dynamic in metadata.get("dynamic_fields", []):
                placeholder = str(dynamic.get("placeholder") or "")
                instruction = str(dynamic.get("field") or "")
                if not placeholder or not instruction:
                    continue
                count = _replace_placeholder_with_field(root, placeholder, instruction)
                if count:
                    changed = True
                    dynamic_counts[instruction] = dynamic_counts.get(instruction, 0) + count
            for adjustment in metadata.get("service_layout", {}).get(
                "preceding_empty_paragraph_font",
                [],
            ):
                marker = format_metadata_value(str(adjustment.get("marker") or ""), metadata)
                font_size_pt = float(adjustment.get("font_size_pt") or 0)
                if not marker or font_size_pt <= 0:
                    continue
                count = _compact_preceding_empty_paragraph(root, marker, font_size_pt)
                if count:
                    changed = True
                    layout_counts[marker] = layout_counts.get(marker, 0) + count
            if (
                name == "word/document.xml"
                and metadata.get("service_layout", {}).get("trim_trailing_empty_paragraphs")
            ):
                count = _trim_trailing_empty_paragraphs(root)
                if count:
                    changed = True
                    layout_counts["trailing_empty_paragraphs"] = count
        if changed:
            parts[name] = etree.tostring(
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
            for name, payload in parts.items():
                package.writestr(name, payload)
        temp_path.replace(output_docx)
    finally:
        temp_path.unlink(missing_ok=True)

    missing_replacements = [
        source for source, count in replacement_counts.items() if count == 0
    ]
    audit = audit_front_matter(output_docx, metadata)
    blockers = [
        *(f"template_replacement_not_found:{item}" for item in missing_replacements),
        *audit["blockers"],
    ]
    report = {
        "status": "PASS" if not blockers else "BLOCKED",
        "input_docx": str(input_docx),
        "input_sha256": sha256_file(input_docx),
        "output_docx": str(output_docx),
        "output_sha256": sha256_file(output_docx),
        "conference_id": metadata["conference_id"],
        "replacement_counts": replacement_counts,
        "dynamic_field_counts": dynamic_counts,
        "layout_adjustment_counts": layout_counts,
        "missing_replacements": missing_replacements,
        "audit": audit,
        "blockers": blockers,
    }
    if report_path is not None:
        _write_json(report_path, report)
    return report


def audit_front_matter(
    docx_path: Path,
    metadata: dict[str, Any],
    report_path: Path | None = None,
) -> dict[str, Any]:
    package_text = _package_audit_text(docx_path)
    folded = package_text.casefold()
    required = {
        marker: folded.count(format_metadata_value(marker, metadata).casefold())
        for marker in metadata["required_markers"]
    }
    stale = {
        marker: folded.count(marker.casefold())
        for marker in metadata["stale_markers"]
        if marker.casefold() in folded
    }
    foreign_ids = sorted(
        {
            int(value)
            for value in re.findall(r"(?:conference\?id=|conf-)(\d+)", folded)
            if int(value) != metadata["conference_id"]
        }
    )
    blockers = [
        *(f"required_front_matter_marker_missing:{marker}" for marker, count in required.items() if not count),
        *(f"stale_front_matter_marker:{marker}:{count}" for marker, count in stale.items()),
        *(f"foreign_conference_identifier:{value}" for value in foreign_ids),
    ]
    report = {
        "status": "PASS" if not blockers else "BLOCKED",
        "conference_id": metadata["conference_id"],
        "docx": str(docx_path),
        "docx_sha256": sha256_file(docx_path),
        "required_marker_counts": required,
        "stale_marker_counts": stale,
        "stale_marker_count": sum(stale.values()),
        "foreign_conference_identifiers": foreign_ids,
        "blockers": blockers,
    }
    if report_path is not None:
        _write_json(report_path, report)
    return report


def _replace_paragraph_text(
    paragraph: etree._Element,
    replacements: list[dict[str, Any]],
) -> dict[str, int]:
    counts = {item["source"]: 0 for item in replacements}
    for replacement in replacements:
        source = replacement["source"]
        while True:
            nodes = paragraph.xpath(".//w:t", namespaces=NS)
            combined = "".join(node.text or "" for node in nodes)
            match = re.search(re.escape(source), combined, flags=re.IGNORECASE)
            if match is None:
                break
            target = _case_adjusted_target(
                match.group(0),
                replacement["target"],
                replacement["preserve_case"],
            )
            _replace_span(nodes, match.start(), match.end(), target)
            counts[source] += 1
    return counts


def _replace_value(
    value: str,
    replacements: list[dict[str, Any]],
) -> tuple[str, dict[str, int]]:
    counts = {item["source"]: 0 for item in replacements}
    updated = value
    for replacement in replacements:
        source = replacement["source"]
        pattern = re.compile(re.escape(source), flags=re.IGNORECASE)

        def replace(match: re.Match[str]) -> str:
            counts[source] += 1
            return _case_adjusted_target(
                match.group(0),
                replacement["target"],
                replacement["preserve_case"],
            )

        updated = pattern.sub(replace, updated)
    return updated, counts


def _replace_span(
    nodes: list[etree._Element],
    start: int,
    end: int,
    replacement: str,
) -> None:
    cursor = 0
    start_index = end_index = -1
    start_offset = end_offset = 0
    for index, node in enumerate(nodes):
        text = node.text or ""
        node_end = cursor + len(text)
        if start_index < 0 and start < node_end:
            start_index = index
            start_offset = start - cursor
        if end <= node_end:
            end_index = index
            end_offset = end - cursor
            break
        cursor = node_end
    if start_index < 0 or end_index < 0:
        raise ValueError("Replacement span could not be mapped to DOCX text nodes")
    prefix = (nodes[start_index].text or "")[:start_offset]
    suffix = (nodes[end_index].text or "")[end_offset:]
    nodes[start_index].text = prefix + replacement + (suffix if start_index == end_index else "")
    _preserve_xml_space(nodes[start_index])
    if start_index != end_index:
        for index in range(start_index + 1, end_index):
            nodes[index].text = ""
        nodes[end_index].text = suffix
        _preserve_xml_space(nodes[end_index])


def _replace_placeholder_with_field(
    root: etree._Element,
    placeholder: str,
    instruction: str,
) -> int:
    count = 0
    for node in list(root.xpath(".//w:t", namespaces=NS)):
        text = node.text or ""
        while placeholder in text:
            run = node.getparent()
            paragraph = run.getparent() if run is not None else None
            if run is None or paragraph is None or run.tag != f"{{{W_NS}}}r":
                break
            before, after = text.split(placeholder, 1)
            node.text = before
            _preserve_xml_space(node)
            field = etree.Element(f"{{{W_NS}}}fldSimple")
            field.set(f"{{{W_NS}}}instr", instruction)
            field_run = etree.SubElement(field, f"{{{W_NS}}}r")
            rpr = run.find("w:rPr", namespaces=NS)
            if rpr is not None:
                field_run.append(deepcopy(rpr))
            field_text = etree.SubElement(field_run, f"{{{W_NS}}}t")
            field_text.text = "0"
            run.addnext(field)
            if after:
                after_run = deepcopy(run)
                after_nodes = after_run.xpath(".//w:t", namespaces=NS)
                for after_node in after_nodes:
                    after_node.text = ""
                if after_nodes:
                    after_nodes[0].text = after
                    _preserve_xml_space(after_nodes[0])
                field.addnext(after_run)
            count += 1
            text = after
            if after:
                node = after_run.xpath(".//w:t", namespaces=NS)[0]
            else:
                break
    return count


def _compact_preceding_empty_paragraph(
    root: etree._Element,
    marker: str,
    font_size_pt: float,
) -> int:
    count = 0
    half_points = str(int(round(font_size_pt * 2)))
    for paragraph in root.xpath(".//w:p", namespaces=NS):
        text = "".join(paragraph.xpath(".//w:t/text()", namespaces=NS)).strip()
        if text.casefold() != marker.casefold():
            continue
        previous = paragraph.getprevious()
        if previous is None or previous.tag != f"{{{W_NS}}}p":
            continue
        previous_text = "".join(previous.xpath(".//w:t/text()", namespaces=NS)).strip()
        if previous_text:
            continue
        ppr = previous.find("w:pPr", namespaces=NS)
        if ppr is None:
            ppr = etree.Element(f"{{{W_NS}}}pPr")
            previous.insert(0, ppr)
        paragraph_rpr = ppr.find("w:rPr", namespaces=NS)
        if paragraph_rpr is None:
            paragraph_rpr = etree.SubElement(ppr, f"{{{W_NS}}}rPr")
        for rpr in [paragraph_rpr, *previous.xpath("./w:r/w:rPr", namespaces=NS)]:
            for element_name in ("sz", "szCs"):
                size = rpr.find(f"w:{element_name}", namespaces=NS)
                if size is None:
                    size = etree.SubElement(rpr, f"{{{W_NS}}}{element_name}")
                size.set(W_VAL, half_points)
        count += 1
    return count


def _trim_trailing_empty_paragraphs(root: etree._Element) -> int:
    bodies = root.xpath("./w:body", namespaces=NS)
    if not bodies:
        return 0
    body = bodies[0]
    removed = 0
    for element in list(reversed(body)):
        if element.tag == f"{{{W_NS}}}sectPr":
            continue
        if element.tag != f"{{{W_NS}}}p":
            break
        text = "".join(element.xpath(".//w:t/text()", namespaces=NS)).strip()
        protected = element.xpath(
            ".//w:br | .//w:instrText | .//w:fldSimple | .//w:drawing | .//w:pict | "
            ".//w:object | .//w:bookmarkStart | ./w:pPr/w:sectPr",
            namespaces=NS,
        )
        if text or protected:
            break
        body.remove(element)
        removed += 1
    return removed


def _case_adjusted_target(source: str, target: str, preserve_case: bool) -> str:
    if preserve_case and any(char.isalpha() for char in source) and source.upper() == source:
        return target.upper()
    return target


def _preserve_xml_space(node: etree._Element) -> None:
    value = node.text or ""
    if value.startswith(" ") or value.endswith(" "):
        node.set(XML_SPACE, "preserve")
    else:
        node.attrib.pop(XML_SPACE, None)


def _package_audit_text(path: Path) -> str:
    values: list[str] = []
    parser = etree.XMLParser(remove_blank_text=False, resolve_entities=False)
    with zipfile.ZipFile(path) as package:
        for name in package.namelist():
            if not name.endswith((".xml", ".rels")):
                continue
            try:
                root = etree.fromstring(package.read(name), parser)
            except etree.XMLSyntaxError:
                continue
            values.extend(str(value) for value in root.xpath(".//w:t/text()", namespaces=NS))
            values.extend(
                str(value)
                for value in root.xpath("//@Target")
                if isinstance(value, str)
            )
    return "\n".join(values)


def _merge_counts(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
