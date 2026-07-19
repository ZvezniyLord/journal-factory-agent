from __future__ import annotations

from pathlib import Path
from typing import Any
import json


REQUIRED_STRING_FIELDS = (
    "event_title",
    "dates",
    "location",
    "conference_url",
    "doi_url",
    "isbn",
    "udc",
    "typography_profile",
)


def load_conference_metadata(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version_must_equal_1")
    if not isinstance(payload.get("conference_id"), int) or payload["conference_id"] <= 0:
        errors.append("conference_id_must_be_positive_integer")
    for field in REQUIRED_STRING_FIELDS:
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            errors.append(f"required_string_missing:{field}")

    replacements = payload.get("template_replacements")
    if not isinstance(replacements, list) or not replacements:
        errors.append("template_replacements_must_be_nonempty_array")
    else:
        for index, replacement in enumerate(replacements):
            if not isinstance(replacement, dict):
                errors.append(f"template_replacement_invalid:{index}")
                continue
            if not str(replacement.get("source") or "").strip():
                errors.append(f"template_replacement_source_missing:{index}")
            if not str(replacement.get("target") or "").strip():
                errors.append(f"template_replacement_target_missing:{index}")

    for field in ("required_markers", "stale_markers"):
        value = payload.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            errors.append(f"{field}_must_be_nonempty_string_array")

    if errors:
        raise ValueError("Invalid conference metadata: " + "; ".join(errors))
    return payload


def format_metadata_value(value: str, metadata: dict[str, Any]) -> str:
    values = {
        key: str(item)
        for key, item in metadata.items()
        if isinstance(item, (str, int, float))
    }
    try:
        return value.format_map(values)
    except KeyError as exc:
        raise ValueError(f"Unknown conference metadata placeholder: {exc.args[0]}") from exc
