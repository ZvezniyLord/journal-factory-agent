from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass


class LLMReviewError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMConfig:
    endpoint: str
    model: str
    timeout_seconds: int = 90


def review_ambiguous_match(config: LLMConfig, payload: dict) -> dict:
    """Request a bounded JSON recommendation. The answer never upgrades a release gate to PASS."""
    candidates = []
    for row in payload.get("alternatives", [])[:3]:
        candidates.append({
            "raw_path": row.get("raw_path"),
            "score": row.get("score"),
            "title_score": row.get("title_score"),
            "author_score": row.get("author_score"),
            "body_score": row.get("body_score"),
        })
    user_payload = {
        "article_id": payload.get("article_id"),
        "golden_title": str(payload.get("golden_title", ""))[:500],
        "golden_authors": payload.get("golden_authors", []),
        "candidates": candidates,
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You are a local review assistant. Select a candidate only when evidence is decisive. "
                "Return JSON only with decision, selected_raw_path, confidence, reason. "
                "decision must be SELECT or REVIEW. Never invent files or edit article text."
            ),
        },
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]
    body = json.dumps({
        "model": config.model,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    url = config.endpoint.rstrip("/") + "/v1/chat/completions"
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            envelope = json.load(response)
        content = envelope["choices"][0]["message"]["content"]
        result = json.loads(content)
    except Exception as exc:  # noqa: BLE001
        raise LLMReviewError(f"LLM_REVIEW_FAILED:{type(exc).__name__}:{exc}") from exc
    if result.get("decision") not in {"SELECT", "REVIEW"}:
        raise LLMReviewError("LLM_INVALID_DECISION")
    allowed = {row["raw_path"] for row in candidates}
    if result.get("decision") == "SELECT" and result.get("selected_raw_path") not in allowed:
        raise LLMReviewError("LLM_SELECTED_UNKNOWN_PATH")
    return {
        "status": "SUGGESTION_ONLY",
        "decision": result.get("decision"),
        "selected_raw_path": result.get("selected_raw_path"),
        "confidence": result.get("confidence"),
        "reason": str(result.get("reason", ""))[:1000],
        "model": config.model,
        "endpoint": config.endpoint,
    }
