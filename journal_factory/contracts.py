from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DECISION_TYPES = {
    "udc_proposal",
    "article_file_match_review",
    "frontmatter_role_classification",
    "reference_boundary_review",
    "caption_role_review",
    "section_mapping_review",
}
DECISION_STATUSES = {"accepted", "rejected", "needs_operator_review", "blocked"}
REQUIRED_DECISION_FIELDS = {
    "decision_type",
    "article_id",
    "status",
    "value",
    "confidence",
    "evidence",
    "model",
    "prompt_version",
    "source_hash",
}


def load_agent_decisions(path: Path | None) -> tuple[dict[str, Any] | None, list[str]]:
    if path is None:
        return None, []
    if not path.exists():
        return None, [f"agent_decisions_missing:{path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return None, [f"agent_decisions_invalid_json:{exc.msg}"]
    errors = validate_agent_decision_bundle(payload)
    return payload, errors


def validate_agent_decision_bundle(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["agent_decisions_not_object"]
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        return ["decisions_not_array"]
    for index, decision in enumerate(decisions):
        prefix = f"decisions[{index}]"
        if not isinstance(decision, dict):
            errors.append(f"{prefix}:not_object")
            continue
        missing = sorted(REQUIRED_DECISION_FIELDS - decision.keys())
        errors.extend(f"{prefix}:missing_{field}" for field in missing)
        decision_type = decision.get("decision_type")
        if decision_type not in DECISION_TYPES:
            errors.append(f"{prefix}:invalid_decision_type")
        if decision.get("status") not in DECISION_STATUSES:
            errors.append(f"{prefix}:invalid_status")
        confidence = decision.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            errors.append(f"{prefix}:invalid_confidence")
        evidence = decision.get("evidence")
        if not isinstance(evidence, list) or not all(isinstance(item, str) for item in evidence):
            errors.append(f"{prefix}:invalid_evidence")
        for field in ["article_id", "model", "prompt_version", "source_hash"]:
            if not isinstance(decision.get(field), str) or not decision.get(field):
                errors.append(f"{prefix}:invalid_{field}")
    return errors
