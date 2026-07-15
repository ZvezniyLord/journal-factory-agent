from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re

from .ingest import ArchiveEntry


@dataclass
class ArticleAudit:
    path: str
    status: str
    text_chars: int
    has_udc: bool
    has_references: bool
    object_risk: str
    issues: list[str]


def audit_article(entry: ArchiveEntry, text: str) -> ArticleAudit:
    issues: list[str] = []
    has_udc = bool(re.search(r"\b(УДК|UDC)\b", text, re.IGNORECASE))
    has_references = bool(re.search(r"(список використан|references|літератур)", text, re.IGNORECASE))
    if len(text.strip()) < 200:
        issues.append("short_or_unreadable_text")
    if not has_udc:
        issues.append("missing_udc_marker")
    if not has_references:
        issues.append("missing_references_marker")
    status = "WARN" if issues else "OK"
    return ArticleAudit(entry.path, status, len(text), has_udc, has_references, "unchecked_in_mvp", issues)


def release_gate(preflight: dict, article_audits: list[ArticleAudit]) -> dict:
    critical = []
    warnings = []
    if preflight["status"] != "READY":
        critical.extend(f"preflight:{b['name']}" for b in preflight["blockers"])
    critical.extend(f"article_unreadable:{a.path}" for a in article_audits if "short_or_unreadable_text" in a.issues)
    for audit in article_audits:
        for issue in audit.issues:
            if issue != "short_or_unreadable_text":
                warnings.append(f"{issue}:{audit.path}")
        if audit.object_risk != "none":
            warnings.append(f"object_integrity_unverified:{audit.path}")
    if preflight["status"] != "READY":
        status = "BUILD BLOCKED"
    elif critical:
        status = "FAIL"
    elif warnings:
        status = "REVIEW"
    else:
        status = "PASS"
    return {
        "status": status,
        "critical": critical,
        "warnings": warnings,
        "article_count": len(article_audits),
        "production_ready": status == "PASS",
        "pipeline_mode": "mvp_text_inventory",
        "limitations": [
            "does_not_run_agent_skill_modules",
            "does_not_preserve_tables_or_figures",
            "does_not_build_manifest_ordered_toc",
            "does_not_apply_production_journal_styles",
            "does_not_verify_rendered_pdf_fidelity",
        ],
    }


def write_reports(reports_dir: Path, inventory: list[dict], audits: list[ArticleAudit], gate: dict) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "archive_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    (reports_dir / "article_audit.json").write_text(json.dumps([asdict(a) for a in audits], ensure_ascii=False, indent=2), encoding="utf-8")
    (reports_dir / "final_quality_gate.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# QA Report", "", f"Release status: `{gate['status']}`", "", f"Articles audited: {len(audits)}", ""]
    lines += [
        f"Production ready: `{gate.get('production_ready', False)}`",
        "",
        f"Pipeline mode: `{gate.get('pipeline_mode', 'unknown')}`",
        "",
    ]
    if gate["critical"]:
        lines += ["## Critical", *[f"- {item}" for item in gate["critical"]], ""]
    if gate.get("warnings"):
        lines += ["## Warnings", *[f"- {item}" for item in gate["warnings"]], ""]
    if gate.get("limitations"):
        lines += ["## MVP Limitations", *[f"- {item}" for item in gate["limitations"]], ""]
    (reports_dir / "QA_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
