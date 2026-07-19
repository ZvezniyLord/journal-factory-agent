from __future__ import annotations

from dataclasses import asdict
from copy import deepcopy
from pathlib import Path
from typing import Any
import json

from .archive_workspace import prepare_archive_workspace, sha256_file
from .article_preparation import prepare_article_source
from .builder_fidelity import audit_sources_in_final
from .conference_metadata import load_conference_metadata
from .config import AppConfig, ensure_dirs
from .document_composer import compose_articles_into_etalon
from .manifest import build_article_manifest
from .official_toc import load_official_toc, resolve_publication_order
from .preflight import run_preflight, write_preflight
from .source_snapshot import create_source_snapshot, snapshot_docx
from .section_normalization import resolve_article_sections
from .service_pages import audit_front_matter, materialize_service_pages
from .style_bridge import merge_template_styles
from .typography_audit import audit_effective_typography
from .typography_profile import apply_typography_profile


def run_journal_builder(
    conference_id: int,
    source: Path,
    etalon: Path,
    template: Path,
    source_pack: Path,
    output_root: Path,
    typography_profile: str,
    conference_config_path: Path,
    typography_profiles_path: Path = Path("config/typography_profiles.json"),
    section_catalog_path: Path = Path("config/section_catalog.json"),
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
    try:
        conference_metadata = load_conference_metadata(conference_config_path)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"conference_metadata_exception:{type(exc).__name__}:{exc}")
        return _finish(config, conference_id, blockers, None, None, None, None)
    if conference_metadata["conference_id"] != conference_id:
        blockers.append(
            f"conference_metadata_id_mismatch:{conference_metadata['conference_id']}:{conference_id}"
        )
    if conference_metadata["typography_profile"] != typography_profile:
        blockers.append(
            f"typography_profile_config_mismatch:{conference_metadata['typography_profile']}:{typography_profile}"
        )
    if blockers:
        return _finish(config, conference_id, blockers, None, None, None, None)
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

    official_toc: dict[str, Any] | None = None
    publication_report: dict[str, Any] | None = None
    publication_config = conference_metadata.get("publication_reference")
    if publication_config:
        reference_value = str(publication_config.get("official_toc") or "").strip()
        if not reference_value:
            blockers.append("publication_reference_official_toc_missing")
            return _finish(config, conference_id, blockers, manifest, None, None, None)
        reference_path = Path(reference_value)
        if not reference_path.is_absolute():
            reference_path = conference_config_path.parent / reference_path
        try:
            official_toc = load_official_toc(reference_path)
            if int(official_toc.get("conference_id") or 0) != conference_id:
                raise ValueError(
                    f"official_toc_conference_id:{official_toc.get('conference_id')}:{conference_id}"
                )
            manifest, publication_report = resolve_publication_order(manifest, official_toc)
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"publication_order_exception:{type(exc).__name__}:{exc}")
            return _finish(config, conference_id, blockers, manifest, None, None, None)
        _write_json(reports_dir / "official_toc.json", official_toc)
        _write_json(reports_dir / "official_corpus_parity.json", publication_report)
        _write_json(reports_dir / "article_manifest.json", manifest)
        if publication_report["status"] != "PASS":
            blockers.extend(
                f"publication_order:{item}" for item in publication_report["blockers"]
            )
            return _finish(config, conference_id, blockers, manifest, None, None, None)

    ordered_articles = sorted(
        manifest["articles"],
        key=lambda item: (item.get("journal_order") is None, item.get("journal_order") or 10**9),
    )
    try:
        section_report = resolve_article_sections(
            ordered_articles,
            workspace_source,
            section_catalog_path,
        )
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"section_normalization_exception:{type(exc).__name__}:{exc}")
        return _finish(config, conference_id, blockers, manifest, None, None, None)
    _write_json(reports_dir / "section_normalization_report.json", section_report)
    if section_report["status"] != "PASS":
        blockers.extend(f"section:{item}" for item in section_report["blockers"])
        return _finish(config, conference_id, blockers, manifest, None, None, None)
    sections_by_article = {
        item["article_id"]: item for item in section_report["articles"]
    }
    source_snapshots: list[dict[str, Any]] = []
    compose_jobs: list[dict[str, Any]] = []
    preparation_reports: list[dict[str, Any]] = []
    snapshots_root = build_dir / "snapshots"
    prepared_root = build_dir / "prepared_articles"

    for article in ordered_articles:
        if article.get("match_status") != "MATCHED":
            blockers.append(f"article_not_matched:{article.get('article_id')}")
            continue
        source_file = workspace_source / article["source_path"]
        if source_file.suffix.lower() != ".docx":
            blockers.append(f"legacy_or_unsupported_article:{article['source_path']}")
            continue
        try:
            raw_snapshot = create_source_snapshot(
                source_file,
                article["article_id"],
                snapshots_root,
                workspace_source,
            )
            prepared_file, preparation_report = prepare_article_source(
                source_file,
                article,
                prepared_root,
            )
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"snapshot_exception:{article['article_id']}:{type(exc).__name__}:{exc}")
            continue
        preparation_reports.append(preparation_report)
        if raw_snapshot.get("snapshot_status") != "PASS":
            blockers.extend(
                f"snapshot:{article['article_id']}:{item}"
                for item in raw_snapshot.get("blockers", [])
            )
        if preparation_report["status"] != "PASS":
            blockers.extend(
                f"preparation:{article['article_id']}:{item}"
                for item in preparation_report.get("blockers", [])
            )
        if prepared_file == source_file:
            fidelity_snapshot = raw_snapshot
        else:
            fidelity_snapshot = create_source_snapshot(
                prepared_file,
                f"{article['article_id']}-prepared",
                snapshots_root,
                prepared_root,
            )
            fidelity_snapshot["source_path"] = f"{article['source_path']}#prepared"
        source_snapshots.append(fidelity_snapshot)
        compose_jobs.append(
            {
                "article_id": article["article_id"],
                "source_file": str(prepared_file),
                "section": sections_by_article[article["article_id"]]["display_title"],
                "section_key": sections_by_article[article["article_id"]]["canonical_key"],
                "section_order": sections_by_article[article["article_id"]]["section_order"],
                "journal_order": article.get("journal_order"),
                "title_bookmark": preparation_report.get("title_bookmark"),
            }
        )

    _write_json(
        reports_dir / "article_preparation_report.json",
        {
            "status": "PASS" if not any(item["status"] != "PASS" for item in preparation_reports) else "BLOCKED",
            "articles": preparation_reports,
            "article_count": len(preparation_reports),
        },
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

    service_master = build_dir / "workspace" / "ETALON_WITH_CONFERENCE_METADATA.docx"
    try:
        service_metadata = deepcopy(conference_metadata)
        if official_toc is not None:
            service_metadata["official_toc"] = official_toc
        front_matter_report = materialize_service_pages(
            typography_master,
            service_master,
            service_metadata,
            reports_dir / "front_matter_materialization_report.json",
        )
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"front_matter_exception:{type(exc).__name__}:{exc}")
        return _finish(config, conference_id, blockers, manifest, style_report, None, None)
    if front_matter_report["status"] != "PASS":
        blockers.extend(f"front_matter:{item}" for item in front_matter_report["blockers"])
        return _finish(config, conference_id, blockers, manifest, style_report, None, None)

    output_docx = build_dir / f"Conference{conference_id}_generated.docx"
    try:
        pagination_policy = deepcopy((official_toc or {}).get("page_numbering") or {})
        if publication_config and publication_config.get("word_compatibility_mode") is not None:
            pagination_policy["word_compatibility_mode"] = int(
                publication_config["word_compatibility_mode"]
            )
        compose_report = compose_articles_into_etalon(
            service_master,
            compose_jobs,
            output_docx,
            pagination_policy=pagination_policy or None,
            layout_adjustments=(official_toc or {}).get("layout_adjustments"),
        )
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"compose_exception:{type(exc).__name__}:{exc}")
        return _finish(config, conference_id, blockers, manifest, style_report, None, None)

    _write_json(reports_dir / "compose_report.json", compose_report)
    if compose_report["status"] != "PASS":
        blockers.extend(f"compose:{item}" for item in compose_report.get("blockers", []))
        return _finish(config, conference_id, blockers, manifest, style_report, compose_report, None)

    final_front_matter_report = audit_front_matter(
        output_docx,
        service_metadata,
        reports_dir / "front_matter_audit.json",
    )
    if final_front_matter_report["status"] != "PASS":
        blockers.extend(f"front_matter_audit:{item}" for item in final_front_matter_report["blockers"])

    typography_audit = audit_effective_typography(
        output_docx,
        typography_profiles_path,
        typography_profile,
        reports_dir / "typography_audit.json",
    )
    if typography_audit["status"] != "PASS":
        blockers.extend(f"typography_audit:{item}" for item in typography_audit["blockers"])

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
        quality_reports={
            "front_matter": final_front_matter_report,
            "sections": section_report,
            "typography": typography_audit,
            "publication": publication_report or {},
        },
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
    quality_reports: dict[str, dict[str, Any]] | None = None,
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
        "front_matter_status": (quality_reports or {}).get("front_matter", {}).get("status"),
        "section_normalization_status": (quality_reports or {}).get("sections", {}).get("status"),
        "typography_audit_status": (quality_reports or {}).get("typography", {}).get("status"),
        "publication_order_status": (quality_reports or {}).get("publication", {}).get("status"),
        "blockers": blockers,
        "required_next_gates": [
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
