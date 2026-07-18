from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import json

from .archive_workspace import prepare_archive_workspace, sha256_file
from .builder_fidelity import audit_sources_in_final
from .config import AppConfig, ensure_dirs
from .document_composer import compose_articles_into_etalon
from .manifest import build_article_manifest
from .preflight import run_preflight, write_preflight
from .source_snapshot import create_source_snapshot, snapshot_docx
from .style_bridge import merge_template_styles
from .typography_profile import apply_typography_profile


def run_journal_builder(
    conference_id: int,
    source: Path,
    etalon: Path,
    template: Path,
    source_pack: Path,
    output_root: Path,
    typography_profile: str,
    typography_profiles_path: Path = Path("config/typography_profiles.json"),
) -> dict[str, Any]:
    """Build a real DOCX draft from RAW articles with fail-closed fidelity gates."""
    build_dir = output_root / f"Conference{conference_id}"
    reports_dir = build_dir / "reports"
    config = AppConfig(
        mode="production",
        archive=source,
        etalon=etalon,
        template=template,
        source_pack=source_pack,
        build_dir=build_dir,
        reports_dir=reports_dir,
    )
    ensure_dirs(config)

    blockers: list[str] = []
    preflight = run_preflight(config)
    write_preflight(config, preflight)
    if preflight["status"] != "READY":
        blockers.extend(f"preflight:{item['name']}" for item in preflight["blockers"])
        return _finish(config, conference_id, blockers, None, None, None, None)

    try:
        inventory = prepare_archive_workspace(source, build_dir / "workspace", reports_dir)
        workspace_source = Path(inventory["workspace_source"])
        manifest = build_article_manifest(workspace_source, reports_dir)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"ingest_or_manifest_exception:{type(exc).__name__}:{exc}")
        return _finish(config, conference_id, blockers, None, None, None, None)

    if manifest["manifest_status"] != "PASS":
        blockers.extend(f"manifest:{item}" for item in manifest.get("blockers", []))
        return _finish(config, conference_id, blockers, manifest, None, None, None)

    ordered_articles = sorted(
        manifest["articles"],
        key=lambda item: (item.get("journal_order") is None, item.get("journal_order") or 10**9),
    )
    source_snapshots: list[dict[str, Any]] = []
    compose_jobs: list[dict[str, Any]] = []
    snapshots_root = build_dir / "snapshots"

    for article in ordered_articles:
        if article.get("match_status") != "MATCHED":
            blockers.append(f"article_not_matched:{article.get('article_id')}")
            continue
        source_file = workspace_source / article["source_path"]
        if source_file.suffix.lower() != ".docx":
            blockers.append(f"legacy_or_unsupported_article:{article['source_path']}")
            continue
        try:
            snapshot = create_source_snapshot(
                source_file,
                article["article_id"],
                snapshots_root,
                workspace_source,
            )
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"snapshot_exception:{article['article_id']}:{type(exc).__name__}:{exc}")
            continue
        source_snapshots.append(snapshot)
        if snapshot.get("snapshot_status") != "PASS":
            blockers.extend(
                f"snapshot:{article['article_id']}:{item}"
                for item in snapshot.get("blockers", [])
            )
        compose_jobs.append(
            {
                "article_id": article["article_id"],
                "source_file": str(source_file),
                "section": article.get("section_raw") or article.get("section_id") or "",
                "journal_order": article.get("journal_order"),
            }
        )

    if blockers:
        return _finish(config, conference_id, blockers, manifest, None, None, None)

    styled_master = build_dir / "workspace" / "ETALON_WITH_JURNAL_STYLES.docx"
    style_report = merge_template_styles(
        etalon,
        template,
        styled_master,
        reports_dir / "style_bridge_report.json",
    )
    if style_report["status"] != "PASS":
        blockers.extend(f"style:{item}" for item in style_report["missing_required_style_names"])
        return _finish(config, conference_id, blockers, manifest, style_report, None, None)

    typography_master = build_dir / "workspace" / "ETALON_WITH_TYPOGRAPHY_PROFILE.docx"
    try:
        typography_report = apply_typography_profile(
            styled_master,
            typography_master,
            typography_profiles_path,
            typography_profile,
            reports_dir / "typography_profile_report.json",
        )
        style_report["typography"] = typography_report
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"typography_profile_exception:{type(exc).__name__}:{exc}")
        return _finish(config, conference_id, blockers, manifest, style_report, None, None)

    output_docx = build_dir / f"Conference{conference_id}_generated.docx"
    try:
        compose_report = compose_articles_into_etalon(typography_master, compose_jobs, output_docx)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"compose_exception:{type(exc).__name__}:{exc}")
        return _finish(config, conference_id, blockers, manifest, style_report, None, None)

    _write_json(reports_dir / "compose_report.json", compose_report)
    if compose_report["status"] != "PASS":
        blockers.extend(f"compose:{item}" for item in compose_report.get("blockers", []))
        return _finish(config, conference_id, blockers, manifest, style_report, compose_report, None)

    final_snapshot = snapshot_docx(output_docx, output_docx.parent)
    _write_json(reports_dir / "final_docx_snapshot.json", final_snapshot)
    fidelity_report = audit_sources_in_final(source_snapshots, final_snapshot)
    _write_json(reports_dir / "fidelity_report.json", fidelity_report)
    if fidelity_report["status"] != "PASS":
        blockers.extend(f"fidelity:{item}" for item in fidelity_report.get("blockers", []))

    if len(compose_report.get("inserted", [])) != manifest["article_count"]:
        blockers.append(
            f"article_count_mismatch:{len(compose_report.get('inserted', []))}:{manifest['article_count']}"
        )

    return _finish(
        config,
        conference_id,
        blockers,
        manifest,
        style_report,
        compose_report,
        fidelity_report,
        output_docx=output_docx,
    )


def _finish(
    config: AppConfig,
    conference_id: int,
    blockers: list[str],
    manifest: dict[str, Any] | None,
    style_report: dict[str, Any] | None,
    compose_report: dict[str, Any] | None,
    fidelity_report: dict[str, Any] | None,
    output_docx: Path | None = None,
) -> dict[str, Any]:
    build_succeeded = output_docx is not None and output_docx.is_file() and not blockers
    status = "DRAFT_BUILT" if build_succeeded else "BUILD BLOCKED"
    typography_report = style_report.get("typography") if style_report else None
    gate = {
        "conference_id": conference_id,
        "status": status,
        "production_ready": False,
        "output_docx": str(output_docx) if output_docx else None,
        "output_sha256": sha256_file(output_docx) if output_docx and output_docx.is_file() else None,
        "article_count": manifest.get("article_count", 0) if manifest else 0,
        "style_status": style_report.get("status") if style_report else None,
        "typography_profile": typography_report.get("profile") if typography_report else None,
        "body_font_size_pt": typography_report.get("body_font_size_pt") if typography_report else None,
        "compose_status": compose_report.get("status") if compose_report else None,
        "fidelity_status": fidelity_report.get("status") if fidelity_report else None,
        "blockers": blockers,
        "required_next_gates": [
            "HEADER_NORMALIZATION_PLAN",
            "DIRECT_RUN_FONT_SIZE_AUDIT",
            "TOC_GENERATION",
            "DOCX_TO_PDF_RENDER",
            "PAGINATION_CONVERGENCE",
            "PUBLICATION_PARITY",
            "CLEAN_REBUILD",
        ],
    }
    _write_json(config.reports_dir / "journal_builder_gate.json", gate)
    result = {
        "status": status,
        "draft": str(output_docx) if output_docx else None,
        "articles": gate["article_count"],
        "gate": gate,
        "config": asdict(config),
    }
    _write_json(config.reports_dir / "journal_builder_result.json", result)
    return result


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
