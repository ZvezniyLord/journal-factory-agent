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
