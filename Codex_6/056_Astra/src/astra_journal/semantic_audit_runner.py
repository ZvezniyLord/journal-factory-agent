from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .bootstrap import load_runtime
from .hermes.cache import DiskHermesCache, make_cache_key
from .hermes.envelope import EnvelopeValidationError, validate_envelope
from .hermes.routing import HermesRouter
from .hermes_client import HermesEndpoint, HermesError
from .semantic_packets import (
    SEMANTIC_PACKET_VERSION,
    article_semantic_instruction,
    build_article_semantic_packet,
)


PROMPT_VERSION = "article-semantic-audit-v1"
SCHEMA_VERSION = "1"


class SemanticAuditBlocked(RuntimeError):
    pass


def _endpoint_from(runtime: dict[str, Any], key: str) -> HermesEndpoint:
    cfg = runtime[key]
    return HermesEndpoint(
        base_url=cfg["openai_base_url"],
        model=cfg["model"],
        context=int(cfg["context"]),
        role=cfg.get("role", key),
    )


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    tmp.replace(path)


def _runtime_fingerprint(runtime: dict[str, Any]) -> str:
    stable = json.dumps(
        runtime,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(stable).hexdigest()


def _model_signature(runtime: dict[str, Any]) -> str:
    return "|".join(
        str(runtime[k]["model"])
        for k in ("main", "fallback")
        if k in runtime
    )


def _coauthors_for(
    item: dict[str, Any],
    materials: list[dict[str, Any]],
) -> list[str]:
    title = str(item.get("title_raw") or "").strip()
    section = str(item.get("section_raw") or "").strip()
    result: list[str] = []
    for other in materials:
        if other.get("match_status") != "COAUTHOR":
            continue
        if str(other.get("title_raw") or "").strip() != title:
            continue
        if str(other.get("section_raw") or "").strip() != section:
            continue
        value = str(other.get("authors_raw") or "").strip()
        if value:
            result.append(value)
    return result


def _write_ambiguities(path: Path, payload: dict[str, Any]) -> None:
    lines = ["# Semantic audit ambiguities", ""]
    for record in payload.get("articles", []):
        result = record.get("result") or {}
        ambiguities = result.get("ambiguities") or []
        if record.get("status") not in {"ok", "cached", "deferred"} or ambiguities:
            lines.append(f"## {record.get('source_path')}")
            lines.append(f"- status: {record.get('status')}")
            if record.get("error"):
                lines.append(f"- error: {record.get('error')}")
            for value in ambiguities:
                lines.append(f"- {value}")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run_stateless_semantic_audit(
    *,
    root: str | Path,
    manifest_path: str | Path,
    source_index_path: str | Path,
    run_dir: str | Path,
    max_new_articles: int | None = None,
) -> dict[str, Any]:
    project_root = Path(root).resolve()
    run_root = Path(run_dir).resolve()
    run_root.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    source_index = json.loads(Path(source_index_path).read_text(encoding="utf-8"))
    runtime = load_runtime(project_root)

    limits = runtime.get("limits", {})
    timeout = float(limits.get("timeout_seconds", 120))
    max_output = int(limits.get("article_semantic_max_output_tokens", 1200))
    max_input_chars = int(limits.get("article_semantic_max_input_chars", 16000))
    max_request_chars = int(limits.get("article_semantic_max_request_chars", 20000))
    max_retries = int(limits.get("article_semantic_max_retries", 0))
    if max_new_articles is None:
        max_new_articles = int(
            limits.get("article_semantic_max_new_articles_per_process", 3)
        )
    max_new_articles = max(1, int(max_new_articles))

    if int(limits.get("article_semantic_batch_size", 1)) != 1:
        raise SemanticAuditBlocked("ARTICLE_SEMANTIC_BATCH_SIZE_MUST_BE_1")

    endpoints = [
        (key, _endpoint_from(runtime, key))
        for key in ("main", "fallback")
        if key in runtime
    ]
    if not endpoints:
        raise SemanticAuditBlocked("NO_HERMES_ENDPOINTS_CONFIGURED")

    router = HermesRouter(
        endpoints,
        timeout=timeout,
        api_key=os.getenv("HERMES_API_KEY") or None,
        max_retries=max_retries,
        retry_delay_s=0.25,
    )

    records_by_path = {
        str(record.get("path")): record
        for record in source_index.get("records", [])
        if record.get("path")
    }
    materials = list(manifest.get("materials", []))
    matched = [m for m in materials if m.get("match_status") == "MATCHED"]

    response_dir = run_root / "hermes" / "responses"
    response_dir.mkdir(parents=True, exist_ok=True)
    cache = DiskHermesCache(run_root / "hermes" / "cache")

    audit_path = run_root / "semantic_audit.json"
    ambiguities_path = run_root / "ambiguities.md"
    config_fp = _runtime_fingerprint(runtime)
    model_sig = _model_signature(runtime)

    output: dict[str, Any] = {
        "architecture": "STATELESS_ONE_ARTICLE_PER_REQUEST",
        "packet_version": SEMANTIC_PACKET_VERSION,
        "prompt_version": PROMPT_VERSION,
        "article_count": len(matched),
        "completed": 0,
        "cached": 0,
        "failed": 0,
        "articles": [],
        "max_new_articles_this_process": max_new_articles,
        "new_requests_this_process": 0,
    }

    new_requests = 0
    for ordinal, item in enumerate(matched, start=1):
        source_path = str(item.get("matched_source") or "")
        source = records_by_path.get(source_path)
        record_out: dict[str, Any] = {
            "ordinal": ordinal,
            "source_path": source_path,
            "excel_row": item.get("excel_row"),
            "status": "pending",
        }

        if source is None:
            record_out["status"] = "fail"
            record_out["error"] = "MATCHED_SOURCE_NOT_IN_SOURCE_INDEX"
            output["failed"] += 1
            output["articles"].append(record_out)
            _atomic_json(audit_path, output)
            continue

        if not source.get("semantic_signals"):
            record_out["status"] = "fail"
            record_out["error"] = "SOURCE_INDEX_MISSING_SEMANTIC_SIGNALS_REGENERATE_REQUIRED"
            output["failed"] += 1
            output["articles"].append(record_out)
            _atomic_json(audit_path, output)
            continue

        packet_item = dict(item)
        packet_item["coauthors_raw"] = _coauthors_for(item, materials)
        packet = build_article_semantic_packet(
            packet_item,
            source,
            max_chars=max_input_chars,
        )
        key = make_cache_key(
            normalized_input=packet,
            task="article_semantic_audit",
            prompt_version=PROMPT_VERSION,
            schema_version=SCHEMA_VERSION,
            model=model_sig,
            config_fingerprint=config_fp,
        )
        record_out["cache_key"] = key
        record_out["input_chars"] = packet.get("input_chars")

        cached = cache.get(key)
        if cached is not None and isinstance(cached.get("parsed"), dict):
            parsed = cached["parsed"]
            try:
                validate_envelope(parsed, expected_task="article_semantic_audit")
            except EnvelopeValidationError:
                cached = None
            else:
                record_out["status"] = "cached"
                record_out["worker"] = cached.get("worker")
                record_out["result"] = parsed.get("result")
                record_out["confidence"] = parsed.get("confidence")
                record_out["warnings"] = parsed.get("warnings", [])
                output["cached"] += 1
                output["completed"] += 1
                output["articles"].append(record_out)
                _atomic_json(audit_path, output)
                _write_ambiguities(ambiguities_path, output)
                continue

        if new_requests >= max_new_articles:
            record_out["status"] = "deferred"
            output["articles"].append(record_out)
            continue

        instruction = article_semantic_instruction(packet)
        if len(instruction) > max_request_chars:
            record_out["status"] = "fail"
            record_out["error"] = (
                f"SEMANTIC_REQUEST_TOO_LARGE:{len(instruction)}>{max_request_chars}"
            )
            output["failed"] += 1
            output["articles"].append(record_out)
            _atomic_json(audit_path, output)
            _write_ambiguities(ambiguities_path, output)
            continue

        new_requests += 1
        output["new_requests_this_process"] = new_requests
        try:
            routed = router.chat_json(
                task="article_semantic_audit",
                instruction=instruction,
                max_tokens=max_output,
            )
            parsed = validate_envelope(
                routed.parsed,
                expected_task="article_semantic_audit",
            )
            response_payload = {
                "source_path": source_path,
                "cache_key": key,
                "worker": routed.worker,
                "model": routed.endpoint.model,
                "base_url": routed.endpoint.base_url,
                "latency_s": routed.latency_s,
                "attempts": routed.attempts,
                "packet": packet,
                "parsed": parsed,
                "raw_response": routed.raw,
            }
            _atomic_json(
                response_dir / f"{ordinal:04d}.json",
                response_payload,
            )
            cache.put(
                key,
                {
                    "worker": routed.worker,
                    "model": routed.endpoint.model,
                    "parsed": parsed,
                },
            )

            record_out["status"] = "ok"
            record_out["worker"] = routed.worker
            record_out["latency_s"] = round(routed.latency_s, 3)
            record_out["confidence"] = parsed.get("confidence")
            record_out["result"] = parsed.get("result")
            record_out["warnings"] = parsed.get("warnings", [])
            output["completed"] += 1
        except (HermesError, EnvelopeValidationError, ValueError) as exc:
            record_out["status"] = "fail"
            record_out["error"] = str(exc)
            output["failed"] += 1

        output["articles"].append(record_out)
        # Checkpoint after EVERY article. A provider crash never loses completed work.
        _atomic_json(audit_path, output)
        _write_ambiguities(ambiguities_path, output)

    output["remaining"] = max(0, len(matched) - output["completed"])
    if output["remaining"] == 0 and output["failed"] == 0:
        output["status"] = "PASS"
    elif output["completed"] > 0 and output["remaining"] > 0:
        output["status"] = "INCOMPLETE"
    elif output["failed"] > 0:
        output["status"] = "BLOCKED"
    else:
        output["status"] = "INCOMPLETE"

    _atomic_json(audit_path, output)
    _write_ambiguities(ambiguities_path, output)
    return output
