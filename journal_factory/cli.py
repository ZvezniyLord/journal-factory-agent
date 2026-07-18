from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import audit_article, release_gate, write_reports
from .builder_pipeline import run_journal_builder
from .config import default_config, ensure_dirs
from .corpus_cycle import run_conference_cycle, run_series
from .corpus_llm import LLMConfig
from .docx_builder import build_draft
from .ingest import extract_docx_text_from_zip, inventory_archive, inventory_as_dict, is_non_article_text
from .preflight import run_preflight, write_preflight
from .production_pipeline import run_production_build
from .template import style_snapshot, write_style_snapshot
from .webapp import serve


def _resolve_source_path(value: str | None) -> str | None:
    return value or None


def _llm_config(args: argparse.Namespace) -> LLMConfig | None:
    if not getattr(args, "llm_endpoint", None):
        return None
    if not getattr(args, "llm_model", None):
        raise SystemExit("--llm-model is required when --llm-endpoint is set")
    return LLMConfig(args.llm_endpoint, args.llm_model)


def cmd_preflight(args: argparse.Namespace) -> int:
    config = default_config(_resolve_source_path(args.source), args.mode)
    ensure_dirs(config)
    result = run_preflight(config)
    write_preflight(config, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BUILD BLOCKED" else 0


def cmd_build(args: argparse.Namespace) -> int:
    config = default_config(_resolve_source_path(args.source), args.mode)
    ensure_dirs(config)
    if config.mode == "production":
        result = run_production_build(config, args.agent_decisions)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    preflight = run_preflight(config)
    write_preflight(config, preflight)
    entries = inventory_archive(config.archive)
    candidates = [entry for entry in entries if entry.article_candidate]
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
    gate = release_gate(preflight, audits, config.mode)
    write_reports(config.reports_dir, inventory_as_dict(entries), audits, gate)
    print(
        json.dumps(
            {"draft": str(draft), "status": gate["status"], "articles": len(audits)},
            ensure_ascii=False,
            indent=2,
        )
    )
    if gate["status"] == "PASS":
        return 0
    if gate["status"] == "BUILD BLOCKED":
        return 2
    return 1


def cmd_build_journal(args: argparse.Namespace) -> int:
    result = run_journal_builder(
        conference_id=args.conference_id,
        source=args.source,
        etalon=args.etalon,
        template=args.template,
        source_pack=args.source_pack,
        output_root=args.output,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result["status"] == "DRAFT_BUILT" else 2


def cmd_analyze_conference(args: argparse.Namespace) -> int:
    result = run_conference_cycle(
        conference_id=args.conference_id,
        raw_source=args.raw,
        golden_pdf=args.golden,
        output_root=args.output,
        expected_articles=args.expected_articles,
        llm_config=_llm_config(args),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS_ANALYSIS" else 1


def cmd_analyze_series(args: argparse.Namespace) -> int:
    result = run_series(args.manifest, args.output, _llm_config(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["review"] == 0 else 1


def cmd_serve(args: argparse.Namespace) -> int:
    serve(args.host, args.port)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="journal_factory")
    sub = parser.add_subparsers(required=True)

    preflight = sub.add_parser("preflight")
    preflight.add_argument("--source")
    preflight.add_argument("--mode", choices=["diagnostic-mvp", "production"], default="diagnostic-mvp")
    preflight.set_defaults(func=cmd_preflight)

    build = sub.add_parser("build")
    build.add_argument("--source")
    build.add_argument("--mode", choices=["diagnostic-mvp", "production"], default="diagnostic-mvp")
    build.add_argument("--agent-decisions", type=Path)
    build.add_argument("--limit", type=int, default=200)
    build.set_defaults(func=cmd_build)

    journal = sub.add_parser("build-journal")
    journal.add_argument("--conference-id", type=int, required=True)
    journal.add_argument("--source", type=Path, required=True)
    journal.add_argument("--etalon", type=Path, required=True)
    journal.add_argument("--template", type=Path, required=True)
    journal.add_argument("--source-pack", type=Path, required=True)
    journal.add_argument("--output", type=Path, default=Path("build/journal_builder"))
    journal.set_defaults(func=cmd_build_journal)

    analyze = sub.add_parser("analyze-conference")
    analyze.add_argument("--conference-id", type=int, required=True)
    analyze.add_argument("--raw", type=Path, required=True, help="ZIP/RAR archive or extracted directory")
    analyze.add_argument("--golden", type=Path, required=True, help="Official Conference<ID>.pdf")
    analyze.add_argument("--output", type=Path, default=Path("build/corpus_cycles"))
    analyze.add_argument("--expected-articles", type=int)
    analyze.add_argument("--llm-endpoint", help="OpenAI-compatible local endpoint")
    analyze.add_argument("--llm-model", help="Local model; REVIEW suggestions only")
    analyze.set_defaults(func=cmd_analyze_conference)

    series = sub.add_parser("analyze-series")
    series.add_argument("--manifest", type=Path, required=True)
    series.add_argument("--output", type=Path, default=Path("build/corpus_cycles"))
    series.add_argument("--llm-endpoint")
    series.add_argument("--llm-model")
    series.set_defaults(func=cmd_analyze_series)

    server = sub.add_parser("serve")
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8765)
    server.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
