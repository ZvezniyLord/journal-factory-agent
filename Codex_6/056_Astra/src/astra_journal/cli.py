from __future__ import annotations

import argparse
import json
from pathlib import Path

from .word_roundtrip import WordComUnavailable, roundtrip_word, write_roundtrip_report
from .word_stability import inspect_docx, write_report


def main() -> int:
    parser = argparse.ArgumentParser(prog="astra-journal")
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit-docx", help="Audit DOCX style/reopen stability risks")
    audit.add_argument("docx", type=Path)
    audit.add_argument("--json", dest="json_path", type=Path)

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
            args.json_path.parent.mkdir(parents=True, exist_ok=True)
            write_report(args.json_path, report)
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
            args.json_path.parent.mkdir(parents=True, exist_ok=True)
            write_roundtrip_report(args.json_path, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
