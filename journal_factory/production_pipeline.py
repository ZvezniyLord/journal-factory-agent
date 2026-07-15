from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import AppConfig, ensure_dirs
from .preflight import run_preflight, write_preflight


def run_production_build(config: AppConfig, agent_decisions: Path | None = None) -> dict[str, Any]:
    ensure_dirs(config)
    preflight = run_preflight(config)
    write_preflight(config, preflight)
    gate = {
        "status": "BUILD BLOCKED",
        "critical": ["PRODUCTION_PIPELINE_NOT_IMPLEMENTED"],
        "warnings": [],
        "article_count": 0,
        "production_ready": False,
        "pipeline_mode": "production",
        "agent_decisions": str(agent_decisions) if agent_decisions else None,
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
        "blockers": [
            {
                "name": "PRODUCTION_PIPELINE_NOT_IMPLEMENTED",
                "message": "Production mode is reserved for the skill-driven pipeline and is not implemented in PR 1.",
            }
        ],
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
                "- PRODUCTION_PIPELINE_NOT_IMPLEMENTED",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"draft": None, "status": gate["status"], "articles": 0, "gate": gate}
