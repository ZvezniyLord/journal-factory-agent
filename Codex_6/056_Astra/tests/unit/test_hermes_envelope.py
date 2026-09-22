import pytest

from astra_journal.hermes.envelope import (
    EnvelopeValidationError,
    validate_envelope,
)


def test_review_plan_schema_accepts_required_fields() -> None:
    payload = {
        "task": "review_astra_plan",
        "status": "ok",
        "confidence": 0.9,
        "result": {
            "blockers": [],
            "gaps": [],
            "risks": [],
            "missing_tests": [],
            "token_saving_opportunities": [],
            "hermes_delegation_improvements": [],
            "suggested_changes": [],
        },
        "evidence": [],
        "warnings": [],
    }
    assert validate_envelope(payload, expected_task="review_astra_plan") is payload


def test_envelope_rejects_task_mismatch() -> None:
    payload = {
        "task": "other",
        "status": "ok",
        "confidence": 1.0,
        "result": {},
        "evidence": [],
        "warnings": [],
    }
    with pytest.raises(EnvelopeValidationError):
        validate_envelope(payload, expected_task="review_astra_plan")
