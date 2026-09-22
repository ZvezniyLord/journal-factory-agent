from __future__ import annotations

import argparse
import json
from pathlib import Path

from .docx_inspector import inspect_docx_source
from .excel_registry import inspect_excel_registry
from .fixture_factory import create_golden_fixture
from .word_roundtrip import WordComUnavailable, roundtrip_word, write_roundtrip_report
from .word_stability import inspect_docx, write_report


def _write_optional(path: Path | None, payload: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="astra-journal")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit-docx", help="Audit DOCX style/reopen stability risks")
    audit.add_argument("docx", type=Path)
    audit.add_argument("--json", dest="json_path", type=Path)

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

    fixture = sub.add_parser(
        "make-golden-fixture",
        help="Generate synthetic DOCX fixture for golden tests",
    )
    fixture.add_argument("output", type=Path)

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

    if args.command == "make-golden-fixture":
        output = create_golden_fixture(args.output)
        print(json.dumps({"status": "PASS", "output": str(output)}, ensure_ascii=False))
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
