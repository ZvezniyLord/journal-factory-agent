from __future__ import annotations

import argparse
import json
from pathlib import Path

from .doc_converter import DocConversionBlocked, convert_doc_to_docx
from .docx_inspector import inspect_docx_source
from .production_intake import IntakeBlocked, extract_and_inventory, write_intake_result
from .source_index import build_source_index, write_source_index
from .excel_registry import inspect_excel_registry
from .fixture_factory import create_golden_fixture
from .manifest_builder import build_manifest, write_manifest
from .word_list_probe import WordListProbeUnavailable, probe_reference_list_values
from .word_roundtrip import WordComUnavailable, roundtrip_word, write_roundtrip_report
from .word_stability import inspect_docx, write_report


def _write_optional(path: Path | None, payload: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="astra-journal")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit-docx", help="Audit DOCX style/reopen stability risks")
    audit.add_argument("docx", type=Path)
    audit.add_argument("--json", dest="json_path", type=Path)

    intake = sub.add_parser(
        "intake-archive",
        help="Extract and inventory a production archive without mutating source files",
    )
    intake.add_argument("archive", type=Path)
    intake.add_argument("--run-dir", type=Path, required=True)
    intake.add_argument("--seven-zip", default="7z")
    intake.add_argument("--json", dest="json_path", type=Path)

    convert_doc = sub.add_parser(
        "convert-doc",
        help="Convert a legacy .doc working copy to .docx using Microsoft Word",
    )
    convert_doc.add_argument("source", type=Path)
    convert_doc.add_argument("destination", type=Path)

    source_index = sub.add_parser(
        "source-index",
        help="Build compact DOCX source index for matching/Hermes",
    )
    source_index.add_argument("root", type=Path)
    source_index.add_argument("--json", dest="json_path", type=Path)

    inspect_source = sub.add_parser(
        "inspect-source",
        help="Extract compact DOCX forensic metadata for deterministic/Hermes use",
    )
    inspect_source.add_argument("docx", type=Path)
    inspect_source.add_argument("--excerpt-paragraphs", type=int, default=80)
    inspect_source.add_argument("--json", dest="json_path", type=Path)

    inspect_excel = sub.add_parser(
        "inspect-excel",
        help="Inspect Excel participant registry without mutating it",
    )
    inspect_excel.add_argument("xlsx", type=Path)
    inspect_excel.add_argument("--sheet")
    inspect_excel.add_argument("--header-row", type=int, default=1)
    inspect_excel.add_argument("--json", dest="json_path", type=Path)

    manifest = sub.add_parser(
        "build-manifest",
        help="Build production manifest from Excel report + source index JSON",
    )
    manifest.add_argument("excel_json", type=Path)
    manifest.add_argument("source_index_json", type=Path)
    manifest.add_argument("--json", dest="json_path", type=Path, required=True)
    manifest.add_argument("--auto-accept", type=float, default=0.96)

    fixture = sub.add_parser(
        "make-golden-fixture",
        help="Generate synthetic DOCX fixture for golden tests",
    )
    fixture.add_argument("output", type=Path)

    probe = sub.add_parser(
        "word-list-probe",
        help="Read Word-visible list values for REFER paragraphs",
    )
    probe.add_argument("docx", type=Path)
    probe.add_argument("--json", dest="json_path", type=Path)

    roundtrip = sub.add_parser(
        "word-roundtrip",
        help="Save-close-reopen a DOCX through Microsoft Word COM",
    )
    roundtrip.add_argument("source", type=Path)
    roundtrip.add_argument("destination", type=Path)
    roundtrip.add_argument("--json", dest="json_path", type=Path)
    roundtrip.add_argument("--visible", action="store_true")

    args = parser.parse_args()

    if args.command == "audit-docx":
        report = inspect_docx(args.docx)
        if args.json_path:
            write_report(args.json_path, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "intake-archive":
        try:
            result = extract_and_inventory(
                args.archive,
                args.run_dir,
                seven_zip_executable=args.seven_zip,
            )
        except IntakeBlocked as exc:
            print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
            return 4
        payload = {
            "archive_path": result.archive_path,
            "conference_number": result.conference_number,
            "extracted_root": result.extracted_root,
            "registry_candidates": result.registry_candidates,
            "article_candidates": result.article_candidates,
            "questionnaire_candidates": result.questionnaire_candidates,
            "template_candidates": result.template_candidates,
            "warnings": result.warnings,
            "inventory": [item.__dict__ for item in result.inventory],
        }
        if args.json_path:
            write_intake_result(args.json_path, result)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "convert-doc":
        try:
            output = convert_doc_to_docx(args.source, args.destination)
        except DocConversionBlocked as exc:
            print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
            return 5
        print(json.dumps({"status": "PASS", "output": str(output)}, ensure_ascii=False))
        return 0

    if args.command == "source-index":
        payload = build_source_index(args.root)
        if args.json_path:
            write_source_index(args.json_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "inspect-source":
        report = inspect_docx_source(
            args.docx,
            excerpt_paragraphs=args.excerpt_paragraphs,
        )
        _write_optional(args.json_path, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "inspect-excel":
        report = inspect_excel_registry(
            args.xlsx,
            sheet_name=args.sheet,
            header_row=args.header_row,
        )
        _write_optional(args.json_path, report)
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0

    if args.command == "build-manifest":
        excel_report = json.loads(args.excel_json.read_text(encoding="utf-8"))
        source_index = json.loads(args.source_index_json.read_text(encoding="utf-8"))
        payload = build_manifest(
            excel_report,
            source_index,
            auto_accept=args.auto_accept,
        )
        write_manifest(args.json_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return 0

    if args.command == "make-golden-fixture":
        output = create_golden_fixture(args.output)
        print(json.dumps({"status": "PASS", "output": str(output)}, ensure_ascii=False))
        return 0

    if args.command == "word-list-probe":
        try:
            report = probe_reference_list_values(args.docx)
        except WordListProbeUnavailable as exc:
            print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
            return 3
        _write_optional(args.json_path, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.command == "word-roundtrip":
        try:
            report = roundtrip_word(
                args.source,
                args.destination,
                visible=args.visible,
            )
        except WordComUnavailable as exc:
            print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
            return 3
        if args.json_path:
            write_roundtrip_report(args.json_path, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
