from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import AppConfig, ensure_dirs
from .contracts import load_agent_decisions
from .preflight import run_preflight, write_preflight
from .skills_loader import load_skill_registry


def run_production_build(config: AppConfig, agent_decisions: Path | None = None) -> dict[str, Any]:
    ensure_dirs(config)
    preflight = run_preflight(config)
    write_preflight(config, preflight)
    registry = load_skill_registry()
    registry_manifest = registry.to_manifest()
    (config.reports_dir / "active_skill_manifest.json").write_text(
        json.dumps(registry_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    decisions_payload, decision_errors = load_agent_decisions(agent_decisions)

    critical = []
    blockers = []
    if preflight["status"] != "READY":
        critical.extend(f"preflight:{blocker['name']}" for blocker in preflight["blockers"])
        blockers.extend(preflight["blockers"])
    if registry.registry_status != "PASS" or decision_errors:
        critical.append("SKILL_REGISTRY_INVALID")
        blockers.extend({"name": item, "message": item} for item in registry.blockers)
        blockers.extend({"name": item, "message": item} for item in decision_errors)
    if not critical:
        critical.append("NEXT_PHASE_MANIFEST_NOT_IMPLEMENTED")
        blockers.append(
            {
                "name": "NEXT_PHASE_MANIFEST_NOT_IMPLEMENTED",
                "message": "Skill registry and contracts are valid; manifest phase is not implemented in PR 2.",
            }
        )

    gate = {
        "status": "BUILD BLOCKED",
        "critical": critical,
        "warnings": [],
        "article_count": 0,
        "production_ready": False,
        "pipeline_mode": "production",
        "agent_decisions": str(agent_decisions) if agent_decisions else None,
        "agent_decisions_loaded": decisions_payload is not None,
        "agent_decisions_errors": decision_errors,
        "skill_registry_status": registry.registry_status,
        "active_skill_manifest": str(config.reports_dir / "active_skill_manifest.json"),
        "required_phases": [
            "skill_registry",
            "manifest",
            "source_snapshots",
            "frontmatter_udc_styles",
            "references_tables_figures",
            "etalon_assembly",
            "toc_pagination_render",
            "source_to_final_audit",
            "visual_regression",
            "final_release_gate",
        ],
        "blockers": blockers,
    }
    config.reports_dir.mkdir(parents=True, exist_ok=True)
    (config.reports_dir / "final_quality_gate.json").write_text(
        json.dumps(gate, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (config.reports_dir / "QA_REPORT.md").write_text(
        "\n".join(
            [
                "# Production QA Report",
                "",
                "Release status: `BUILD BLOCKED`",
                "",
                "Production ready: `False`",
                "",
                "## Critical",
                *[f"- {item}" for item in critical],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"draft": None, "status": gate["status"], "articles": 0, "gate": gate}
