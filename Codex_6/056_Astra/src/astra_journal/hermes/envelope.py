from __future__ import annotations

from typing import Any

from jsonschema import ValidationError, validate


class EnvelopeValidationError(RuntimeError):
    pass


BASE_ENVELOPE = {
    "type": "object",
    "required": ["task", "status", "confidence", "result", "evidence", "warnings"],
    "properties": {
        "task": {"type": "string", "minLength": 1},
        "status": {"enum": ["ok", "review", "fail", "unknown"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "result": {"type": "object"},
        "evidence": {"type": "array"},
        "warnings": {"type": "array"},
    },
    "additionalProperties": False,
}


TASK_RESULT_SCHEMAS: dict[str, dict[str, Any]] = {
    "article_semantic_audit": {
        "type": "object",
        "required": [
            "source_path",
            "author",
            "coauthors",
            "supervisor",
            "affiliation",
            "position_degree",
            "orcid",
            "title",
            "udc_status",
            "abstract_status",
            "keywords_status",
            "table_caption_count",
            "figure_caption_count",
            "ref_title",
            "references_region",
            "section_raw",
            "section_mapping_status",
            "ambiguities",
        ],
        "properties": {
            "source_path": {"type": ["string", "null"]},
            "author": {"type": ["string", "null"]},
            "coauthors": {"type": "array"},
            "supervisor": {"type": ["string", "null"]},
            "affiliation": {"type": ["string", "null"]},
            "position_degree": {"type": ["string", "null"]},
            "orcid": {"type": ["string", "null"]},
            "title": {"type": ["string", "null"]},
            "udc_status": {"type": "string"},
            "abstract_status": {"type": "string"},
            "keywords_status": {"type": "string"},
            "table_caption_count": {"type": "integer", "minimum": 0},
            "figure_caption_count": {"type": "integer", "minimum": 0},
            "ref_title": {"type": ["string", "null"]},
            "references_region": {"type": "string"},
            "section_raw": {"type": ["string", "null"]},
            "section_mapping_status": {"type": "string"},
            "ambiguities": {"type": "array"},
        },
        "additionalProperties": True,
    },
    "review_astra_plan": {
        "type": "object",
        "required": [
            "blockers",
            "gaps",
            "risks",
            "missing_tests",
            "token_saving_opportunities",
            "hermes_delegation_improvements",
            "suggested_changes",
        ],
        "properties": {
            "blockers": {"type": "array"},
            "gaps": {"type": "array"},
            "risks": {"type": "array"},
            "missing_tests": {"type": "array"},
            "token_saving_opportunities": {"type": "array"},
            "hermes_delegation_improvements": {"type": "array"},
            "suggested_changes": {"type": "array"},
        },
        "additionalProperties": False,
    }
}


def validate_envelope(payload: dict[str, Any], *, expected_task: str | None = None) -> dict[str, Any]:
    try:
        validate(instance=payload, schema=BASE_ENVELOPE)
    except ValidationError as exc:
        raise EnvelopeValidationError(str(exc)) from exc

    task = payload["task"]
    if expected_task is not None and task != expected_task:
        raise EnvelopeValidationError(
            f"Task mismatch: expected {expected_task!r}, got {task!r}"
        )

    result_schema = TASK_RESULT_SCHEMAS.get(task)
    if result_schema is not None:
        try:
            validate(instance=payload["result"], schema=result_schema)
        except ValidationError as exc:
            raise EnvelopeValidationError(
                f"Invalid result schema for {task}: {exc.message}"
            ) from exc

    return payload
