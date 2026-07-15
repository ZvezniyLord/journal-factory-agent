from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .archive_workspace import prepare_archive_workspace
from .manifest import build_article_manifest
from .config import AppConfig, ensure_dirs
from .contracts import load_agent_decisions
from .preflight import run_preflight, write_preflight
from .source_snapshot import create_source_snapshot
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
    warnings = []
    article_count = 0
    manifest_status = None
    snapshot_status = None
    if preflight["status"] != "READY":
        critical.extend(f"preflight:{blocker['name']}" for blocker in preflight["blockers"])
        blockers.extend(preflight["blockers"])
    if registry.registry_status != "PASS":
        critical.append("SKILL_REGISTRY_INVALID")
        blockers.extend({"name": item, "message": item} for item in registry.blockers)
    if decision_errors:
        critical.append("AGENT_DECISIONS_INVALID")
        blockers.extend({"name": item, "message": item} for item in decision_errors)
    if not critical:
        try:
            inventory = prepare_archive_workspace(config.archive, config.build_dir / "workspace", config.reports_dir)
            manifest = build_article_manifest(Path(inventory["workspace_source"]), config.reports_dir)
            article_count = manifest["article_count"]
            manifest_status = manifest["manifest_status"]
            schema_errors = []
            schema_errors.extend(_validate_report_schema(config.reports_dir / "archive_inventory.json", "archive-inventory.schema.json"))
            schema_errors.extend(_validate_report_schema(config.reports_dir / "article_manifest.json", "article-manifest.schema.json"))
            if manifest["manifest_status"] != "PASS" or schema_errors:
                critical.append("MANIFEST_INVALID")
                blockers.extend({"name": item, "message": item} for item in [*manifest["blockers"], *schema_errors])
            else:
                snapshot_errors = _create_and_validate_snapshots(config, manifest, Path(inventory["workspace_source"]))
                snapshot_status = "PASS" if not snapshot_errors else "BLOCKED"
                if snapshot_errors:
                    critical.append("SOURCE_SNAPSHOT_INVALID")
                    blockers.extend({"name": item, "message": item} for item in snapshot_errors)
        except Exception as exc:  # noqa: BLE001
            critical.append("MANIFEST_INVALID")
            blockers.append({"name": f"manifest_exception:{type(exc).__name__}", "message": str(exc)})
    if not critical:
        critical.append("NEXT_PHASE_FRONTMATTER_NOT_IMPLEMENTED")
        blockers.append(
            {
                "name": "NEXT_PHASE_FRONTMATTER_NOT_IMPLEMENTED",
                "message": "Registry, manifest, and source snapshots are valid; frontmatter phase is not implemented in PR 3.",
            }
        )

    gate = {
        "status": "BUILD BLOCKED",
        "critical": critical,
        "warnings": warnings,
        "article_count": article_count,
        "production_ready": False,
        "pipeline_mode": "production",
        "agent_decisions": str(agent_decisions) if agent_decisions else None,
        "agent_decisions_loaded": decisions_payload is not None,
        "agent_decisions_errors": decision_errors,
        "skill_registry_status": registry.registry_status,
        "manifest_status": manifest_status,
        "source_snapshot_status": snapshot_status,
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
    return {"draft": None, "status": gate["status"], "articles": article_count, "gate": gate}


def _create_and_validate_snapshots(config: AppConfig, manifest: dict[str, Any], workspace_source: Path) -> list[str]:
    errors: list[str] = []
    snapshots_root = config.build_dir / "snapshots"
    for article in manifest["articles"]:
        if article["match_status"] != "MATCHED":
            continue
        snapshot = create_source_snapshot(
            workspace_source / article["source_path"],
            article["article_id"],
            snapshots_root,
            workspace_source,
        )
        snapshot_path = snapshots_root / article["article_id"] / "source_snapshot.json"
        errors.extend(_validate_report_schema(snapshot_path, "source-snapshot.schema.json"))
        if snapshot["snapshot_status"] != "PASS":
            errors.extend(f"{article['article_id']}:{item}" for item in snapshot.get("blockers", []))
    return errors


def _validate_report_schema(report_path: Path, schema_name: str) -> list[str]:
    schema_path = Path("schemas") / schema_name
    try:
        from jsonschema import Draft202012Validator, ValidationError

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(payload)
        return []
    except ImportError as exc:
        return [f"schema_validator_unavailable:{type(exc).__name__}:{exc}"]
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        return [f"schema_invalid:{report_path.name}:{type(exc).__name__}:{exc}"]
