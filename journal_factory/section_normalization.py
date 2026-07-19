from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
import json
import re


def resolve_article_sections(
    articles: list[dict[str, Any]],
    workspace_source: Path,
    catalog_path: Path,
) -> dict[str, Any]:
    catalog = _load_catalog(catalog_path)
    participant_titles = _load_participant_titles(workspace_source)
    resolved: list[dict[str, Any]] = []
    blockers: list[str] = []

    for article in articles:
        article_id = str(article.get("article_id") or "")
        raw = str(article.get("section_id") or article.get("section_raw") or "")
        canonical = catalog["aliases"].get(_normalize_label(raw)) if raw else None
        source = "article_manifest"
        title_key = _normalize_title(str(article.get("title_detected") or article.get("title_manifest") or ""))
        participant_candidates = participant_titles.get(title_key, [])
        participant_orders = {item["order"] for item in participant_candidates if item.get("order") is not None}

        if canonical is None and len(participant_orders) == 1:
            canonical = catalog["orders"].get(next(iter(participant_orders)))
            source = "raw_participant_manifest"
        if canonical is None:
            blockers.append(f"section_unresolved:{article_id}:{raw or 'blank'}")
            continue
        if participant_orders and canonical["order"] not in participant_orders:
            blockers.append(
                f"section_conflict:{article_id}:manifest={canonical['order']}:participants={sorted(participant_orders)}"
            )
            continue

        resolved.append(
            {
                "article_id": article_id,
                "journal_order": article.get("journal_order"),
                "raw_label": str(article.get("section_raw") or ""),
                "canonical_key": canonical["key"],
                "canonical_label": canonical["label_uk"],
                "display_title": canonical["display_title"],
                "section_order": canonical["order"],
                "resolution_source": source,
            }
        )

    return {
        "status": "PASS" if not blockers and len(resolved) == len(articles) else "BLOCKED",
        "catalog": str(catalog_path),
        "article_count": len(articles),
        "resolved_count": len(resolved),
        "raw_participant_manifest_title_count": len(participant_titles),
        "articles": resolved,
        "blockers": blockers,
    }


def normalize_section_label(label: str, catalog_path: Path) -> dict[str, Any] | None:
    catalog = _load_catalog(catalog_path)
    return catalog["aliases"].get(_normalize_label(label))


def _load_catalog(path: Path) -> dict[str, dict[Any, dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("sections"), list):
        raise ValueError("Invalid section catalog")
    aliases: dict[str, dict[str, Any]] = {}
    orders: dict[int, dict[str, Any]] = {}
    for item in payload["sections"]:
        order = item.get("order")
        label_uk = str(item.get("label_uk") or "").strip()
        label_en = str(item.get("label_en") or "").strip()
        if not isinstance(order, int) or order < 0 or not label_uk or not label_en:
            raise ValueError(f"Invalid section catalog item: {item}")
        canonical = {
            "key": f"section-{order:02d}",
            "order": order,
            "label_uk": label_uk,
            "label_en": label_en,
            "display_title": label_en.upper(),
        }
        if order in orders:
            raise ValueError(f"Duplicate section order: {order}")
        orders[order] = canonical
        for alias in (label_uk, label_en, *(item.get("aliases") or [])):
            key = _normalize_label(str(alias))
            if key in aliases and aliases[key]["order"] != order:
                raise ValueError(f"Ambiguous section alias: {alias}")
            aliases[key] = canonical
    return {"aliases": aliases, "orders": orders}


def _load_participant_titles(workspace_source: Path) -> dict[str, list[dict[str, Any]]]:
    titles: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in workspace_source.rglob("*.sorted.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        records = payload.get("article_participants_sorted") if isinstance(payload, dict) else None
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict) or record.get("is_placeholder") or record.get("is_free_listener"):
                continue
            title = _normalize_title(str(record.get("article_title") or ""))
            order = record.get("section_order")
            if title and isinstance(order, int):
                titles[title].append({"order": order, "source": str(path)})
    return dict(titles)


def _normalize_label(value: str) -> str:
    value = value.replace("\u00a0", " ")
    value = re.sub(r"^\s*\d+\s*[.)-]?\s*", "", value)
    value = re.sub(r"\s*-\s*", "-", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def _normalize_title(value: str) -> str:
    value = re.sub(r"[^\w\sА-Яа-яІіЇїЄєҐґ]", " ", value.casefold())
    return re.sub(r"\s+", " ", value).strip()
