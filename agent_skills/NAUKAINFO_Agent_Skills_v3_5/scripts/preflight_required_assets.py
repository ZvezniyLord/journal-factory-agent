from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W, "r": R}
REQUIRED_STYLE_IDS = {
    "SECTION", "AUTOR", "pip", "11", "UDC", "TabSEC", "TabPIP",
    "TabTaitl", "TABLETEXT", "REF-TITLE", "REFER", "ad", "af6",
}


def inspect_docx(path: Path) -> dict:
    result = {"path": str(path), "ok": False, "errors": []}
    if not path.is_file():
        result["errors"].append("missing")
        return result
    try:
        with ZipFile(path) as zf:
            styles = etree.fromstring(zf.read("word/styles.xml"))
            doc = etree.fromstring(zf.read("word/document.xml"))
    except (BadZipFile, KeyError, etree.XMLSyntaxError) as exc:
        result["errors"].append(f"invalid_docx:{exc}")
        return result

    style_ids = {
        node.get(f"{{{W}}}styleId")
        for node in styles.xpath("//w:style", namespaces=NS)
    }
    missing_styles = sorted(REQUIRED_STYLE_IDS - style_ids)
    if missing_styles:
        result["errors"].append({"missing_style_ids": missing_styles})

    sects = doc.xpath("//w:sectPr", namespaces=NS)
    if len(sects) != 3:
        result["errors"].append({"section_count": len(sects), "expected": 3})
    if len(sects) >= 2:
        pg = sects[1].find("w:pgNumType", namespaces=NS)
        start = pg.get(f"{{{W}}}start") if pg is not None else None
        if start != "1":
            result["errors"].append({"main_section_page_start": start, "expected": "1"})
        footers = sects[1].xpath("./w:footerReference", namespaces=NS)
        if not footers:
            result["errors"].append("main_section_footer_reference_missing")

    result["ok"] = not result["errors"]
    result["section_count"] = len(sects)
    result["required_styles_found"] = sorted(REQUIRED_STYLE_IDS & style_ids)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()

    required = {
        "etalon": root / "02_TEMPLATES_REQUIRED" / "ETALON-JOURNAL.docx",
        "dotx": root / "02_TEMPLATES_REQUIRED" / "Jurnal.dotx",
        "skill_zip": root / "01_SKILL_JOURNAL" / "NAUKAINFO_Agent_Skills_v3_2.zip",
        "manifest": root / "05_TESTS_QA_AND_SCHEMAS" / "FILE_MANIFEST.json",
        "reference_release": root / "03_REFERENCE_RELEASES" / "JOURNAL_136_FINAL_RELEASE_v33.docx",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    report = {
        "root": str(root),
        "required": {k: str(v) for k, v in required.items()},
        "missing": missing,
        "etalon_inspection": inspect_docx(required["etalon"]),
    }
    report["status"] = "PASS" if not missing and report["etalon_inspection"]["ok"] else "BLOCKED"

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"STATUS: {report['status']}")
        if missing:
            print("Missing:", ", ".join(missing))
        for err in report["etalon_inspection"]["errors"]:
            print("ETALON:", err)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
