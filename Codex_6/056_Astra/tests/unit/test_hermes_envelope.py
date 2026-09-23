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


from astra_journal.hermes.envelope import normalize_envelope


def test_article_semantic_partial_envelope_is_normalized_to_review() -> None:
    payload = {
        "task": "article_semantic_audit",
        "result": {
            "source_path": "article.docx",
            "author": "Author",
            "coauthors": [],
            "supervisor": None,
            "affiliation": None,
            "position_degree": None,
            "orcid": None,
            "title": "Title",
            "udc_status": "present",
            "abstract_status": "present",
            "keywords_status": "present",
            "table_caption_count": 0,
            "figure_caption_count": 0,
            "ref_title": "REFERENCES",
            "references_region": "present",
            "section_raw": "Section",
            "section_mapping_status": "review",
            "ambiguities": [],
        },
    }
    normalized = normalize_envelope(
        payload,
        expected_task="article_semantic_audit",
    )
    assert normalized["status"] == "review"
    assert normalized["confidence"] == 0.0
    assert normalized["evidence"] == []
    assert any(
        "MODEL_ENVELOPE_NORMALIZED_MISSING" in warning
        for warning in normalized["warnings"]
    )
