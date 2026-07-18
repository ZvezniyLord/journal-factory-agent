from __future__ import annotations

import json
import os
import shutil
import stat
from dataclasses import asdict
from pathlib import Path

from .corpus_archive import ArchiveLimits, detect_archive, extract_archive_readonly, list_archive_entries, validate_entries
from .corpus_pdf import validate_pdf
from .corpus_pdf import parse_golden_pdf
from .corpus_llm import LLMConfig, review_ambiguous_match
from .corpus_match import align_articles, profile_raw
from .corpus_extract import extract_tree
from .corpus_utils import atomic_write_json, sha256_file, utc_now

RULESET_VERSION = "conference-cycle-0.1.0"


class ConferenceCycleError(RuntimeError):
    pass


def _manifest(root: Path) -> list[dict]:
    rows = []
    for path in sorted(x for x in root.rglob("*") if x.is_file()):
        rows.append({
            "path": str(path.relative_to(root)),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return rows


def _make_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        mode = path.stat().st_mode
        path.chmod(mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)


def _jsonl_append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run_conference_cycle(
    *,
    conference_id: int,
    raw_source: Path,
    golden_pdf: Path,
    output_root: Path,
    expected_articles: int | None = None,
    llm_config: LLMConfig | None = None,
) -> dict:
    raw_source = raw_source.resolve()
    golden_pdf = golden_pdf.resolve()
    if not raw_source.exists():
        raise FileNotFoundError(raw_source)
    if not golden_pdf.is_file():
        raise FileNotFoundError(golden_pdf)

    raw_sha = sha256_file(raw_source) if raw_source.is_file() else "directory"
    golden_sha = sha256_file(golden_pdf)
    fingerprint = f"c{conference_id:03d}-{raw_sha[:12]}-{golden_sha[:12]}-{RULESET_VERSION}"
    run_dir = output_root / f"Conference{conference_id}" / fingerprint
    report_path = run_dir / "cycle_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["idempotent"] = True
        return report
    if run_dir.exists():
        suffix = utc_now().replace(":", "").replace("+00:00", "Z")
        interrupted = run_dir.with_name(run_dir.name + f".interrupted-{suffix}")
        os.replace(run_dir, interrupted)

    run_dir.mkdir(parents=True, exist_ok=False)
    extracted = run_dir / "raw_extracted"
    archive_validation: dict
    if raw_source.is_dir():
        shutil.copytree(raw_source, extracted)
        archive_validation = {"format": "DIRECTORY", "source_path": str(raw_source)}
    else:
        archive_format = detect_archive(raw_source)
        entries = list_archive_entries(raw_source, archive_format)
        archive_validation = {
            "format": archive_format,
            **validate_entries(entries, raw_source.stat().st_size, ArchiveLimits()),
        }
        atomic_write_json(run_dir / "archive_entries.json", [asdict(row) for row in entries])
        extract_archive_readonly(raw_source, extracted, archive_format)
    _make_read_only(extracted)

    inventory = _manifest(extracted)
    atomic_write_json(run_dir / "raw_inventory.json", inventory)
    (run_dir / "MANIFEST.sha256").write_text(
        "".join(f"{row['sha256']}  {row['path']}\n" for row in inventory),
        encoding="utf-8",
    )

    pdf_validation = validate_pdf(golden_pdf)
    publication, golden_articles, golden_warnings = parse_golden_pdf(golden_pdf, conference_id)
    atomic_write_json(run_dir / "golden_publication.json", publication)
    atomic_write_json(run_dir / "golden_articles.json", [row.to_record() for row in golden_articles])

    documents, extraction_failures = extract_tree(extracted)
    atomic_write_json(run_dir / "raw_documents.json", [row.to_record() for row in documents])
    atomic_write_json(run_dir / "extraction_failures.json", extraction_failures)
    candidates = [row for row in documents if row.is_article_candidate]
    profiles = [profile_raw(row) for row in candidates]
    atomic_write_json(run_dir / "raw_profiles.json", [asdict(row) for row in profiles])

    alignments = align_articles(golden_articles, profiles)
    alignment_rows = [row.to_record() for row in alignments]
    llm_suggestions = []
    if llm_config:
        for row in alignment_rows:
            if row["status"] == "REVIEW":
                try:
                    llm_suggestions.append({
                        "article_id": row["article_id"],
                        **review_ambiguous_match(llm_config, row),
                    })
                except Exception as exc:  # noqa: BLE001
                    llm_suggestions.append({
                        "article_id": row["article_id"],
                        "status": "LLM_REVIEW_FAILED",
                        "error": f"{type(exc).__name__}:{exc}",
                    })
    atomic_write_json(run_dir / "alignment.json", alignment_rows)
    atomic_write_json(run_dir / "llm_suggestions.json", llm_suggestions)

    counts = {
        "MATCHED_HIGH": sum(row.status == "MATCHED_HIGH" for row in alignments),
        "REVIEW": sum(row.status == "REVIEW" for row in alignments),
        "UNMATCHED": sum(row.status == "UNMATCHED" for row in alignments),
    }
    detected = len(golden_articles)
    expected_ok = expected_articles is None or detected == expected_articles
    coverage = counts["MATCHED_HIGH"] / detected if detected else 0.0
    release_blockers = []
    if not expected_ok:
        release_blockers.append("GOLDEN_ARTICLE_COUNT_MISMATCH")
    if extraction_failures:
        release_blockers.append("RAW_EXTRACTION_FAILURES")
    if counts["REVIEW"]:
        release_blockers.append("AMBIGUOUS_RAW_MATCHES")
    if counts["UNMATCHED"]:
        release_blockers.append("UNMATCHED_GOLDEN_ARTICLES")
    if golden_warnings:
        release_blockers.append("GOLDEN_SEGMENTATION_WARNINGS")

    status = "PASS_ANALYSIS" if detected and not release_blockers and coverage == 1.0 else "REVIEW"
    report = {
        "schema_version": "1.0",
        "ruleset_version": RULESET_VERSION,
        "conference_id": conference_id,
        "status": status,
        "created_at": utc_now(),
        "idempotent": False,
        "run_dir": str(run_dir),
        "fingerprint": fingerprint,
        "inputs": {
            "raw_source": str(raw_source),
            "raw_sha256": raw_sha,
            "golden_pdf": str(golden_pdf),
            "golden_sha256": golden_sha,
        },
        "archive_validation": archive_validation,
        "pdf_validation": pdf_validation,
        "publication": publication,
        "metrics": {
            "expected_articles": expected_articles,
            "detected_golden_articles": detected,
            "raw_file_count": len(inventory),
            "extractable_documents": len(documents),
            "article_candidates": len(candidates),
            "extraction_failures": len(extraction_failures),
            **counts,
            "high_confidence_coverage": round(coverage, 6),
        },
        "release_blockers": release_blockers,
        "golden_warnings": golden_warnings,
        "llm": {
            "enabled": bool(llm_config),
            "policy": "review-only; suggestions cannot produce PASS",
            "suggestion_count": len(llm_suggestions),
        },
        "next_stage_allowed": status == "PASS_ANALYSIS",
        "claim_limits": [
            "This run proves source alignment only, not a production journal build.",
            "No LLM suggestion can upgrade status to PASS.",
        ],
    }
    atomic_write_json(report_path, report)
    _jsonl_append(output_root / "corpus_metrics.jsonl", {
        "conference_id": conference_id,
        "fingerprint": fingerprint,
        "ruleset_version": RULESET_VERSION,
        "status": status,
        **report["metrics"],
    })
    return report


def run_series(manifest_path: Path, output_root: Path, llm_config: LLMConfig | None = None) -> dict:
    rows = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ConferenceCycleError("SERIES_MANIFEST_MUST_BE_LIST")
    reports = []
    base = manifest_path.resolve().parent

    def resolve_path(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else base / path

    for row in sorted(rows, key=lambda item: int(item["conference_id"])):
        reports.append(run_conference_cycle(
            conference_id=int(row["conference_id"]),
            raw_source=resolve_path(row["raw_source"]),
            golden_pdf=resolve_path(row["golden_pdf"]),
            output_root=output_root,
            expected_articles=row.get("expected_articles"),
            llm_config=llm_config,
        ))
    aggregate = {
        "schema_version": "1.0",
        "ruleset_version": RULESET_VERSION,
        "created_at": utc_now(),
        "conference_count": len(reports),
        "pass_analysis": sum(report["status"] == "PASS_ANALYSIS" for report in reports),
        "review": sum(report["status"] != "PASS_ANALYSIS" for report in reports),
        "mean_high_confidence_coverage": round(
            sum(report["metrics"]["high_confidence_coverage"] for report in reports) / len(reports),
            6,
        ) if reports else 0.0,
        "universal_ruleset": RULESET_VERSION,
        "special_case_count": 0,
        "reports": [{
            "conference_id": report["conference_id"],
            "status": report["status"],
            "fingerprint": report["fingerprint"],
            "metrics": report["metrics"],
            "release_blockers": report["release_blockers"],
        } for report in reports],
    }
    atomic_write_json(output_root / "series_report.json", aggregate)
    return aggregate
