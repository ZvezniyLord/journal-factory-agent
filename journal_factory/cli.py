from __future__ import annotations

import argparse
import json

from .audit import audit_article, release_gate, write_reports
from .config import default_config, ensure_dirs
from .docx_builder import build_draft
from .ingest import extract_docx_text_from_zip, inventory_archive, inventory_as_dict, is_non_article_text
from .preflight import run_preflight, write_preflight
from .template import style_snapshot, write_style_snapshot
from .webapp import serve


def _resolve_source_path(value: str | None) -> str | None:
    return value or None


def cmd_preflight(args: argparse.Namespace) -> int:
    config = default_config(_resolve_source_path(args.source))
    ensure_dirs(config)
    result = run_preflight(config)
    write_preflight(config, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BUILD BLOCKED" else 0


def cmd_build(args: argparse.Namespace) -> int:
    config = default_config(_resolve_source_path(args.source))
    ensure_dirs(config)
    preflight = run_preflight(config)
    write_preflight(config, preflight)

    entries = inventory_archive(config.archive)
    candidates = [e for e in entries if e.article_candidate]
    article_texts = []
    audits = []
    for entry in candidates[: args.limit]:
        text = extract_docx_text_from_zip(config.archive, entry.path)
        if text and is_non_article_text(text):
            continue
        audits.append(audit_article(entry, text))
        if text:
            article_texts.append((entry.path, text))

    snapshot = style_snapshot(config.template)
    write_style_snapshot(snapshot, config.reports_dir / "template_style_snapshot.json")
    draft = build_draft(config.etalon, config.build_dir / "journal_mvp_draft.docx", article_texts)
    gate = release_gate(preflight, audits)
    write_reports(config.reports_dir, inventory_as_dict(entries), audits, gate)
    print(json.dumps({"draft": str(draft), "status": gate["status"], "articles": len(audits)}, ensure_ascii=False, indent=2))
    return 2 if gate["status"] == "BUILD BLOCKED" else (1 if gate["status"] == "FAIL" else 0)


def cmd_serve(args: argparse.Namespace) -> int:
    serve(args.host, args.port)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="journal_factory")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("preflight")
    p.add_argument("--source")
    p.set_defaults(func=cmd_preflight)

    b = sub.add_parser("build")
    b.add_argument("--source")
    b.add_argument("--limit", type=int, default=200)
    b.set_defaults(func=cmd_build)

    s = sub.add_parser("serve")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    s.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
