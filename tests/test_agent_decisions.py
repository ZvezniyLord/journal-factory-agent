from pathlib import Path

from journal_factory.contracts import load_agent_decisions, validate_agent_decision_bundle


def _valid_decision() -> dict:
    return {
        "decision_type": "udc_proposal",
        "article_id": "article-001",
        "status": "needs_operator_review",
        "value": "159.9",
        "confidence": 0.82,
        "evidence": ["title", "keywords"],
        "model": "gemma2:2b",
        "prompt_version": "udc-v1",
        "source_hash": "abc123",
    }


def test_valid_agent_decision_bundle() -> None:
    assert validate_agent_decision_bundle({"decisions": [_valid_decision()]}) == []


def test_invalid_decision_type() -> None:
    decision = _valid_decision()
    decision["decision_type"] = "freeform_edit"

    assert "decisions[0]:invalid_decision_type" in validate_agent_decision_bundle({"decisions": [decision]})


def test_invalid_confidence() -> None:
    decision = _valid_decision()
    decision["confidence"] = 1.5

    assert "decisions[0]:invalid_confidence" in validate_agent_decision_bundle({"decisions": [decision]})


def test_missing_source_hash() -> None:
    decision = _valid_decision()
    del decision["source_hash"]

    errors = validate_agent_decision_bundle({"decisions": [decision]})

    assert "decisions[0]:missing_source_hash" in errors
    assert "decisions[0]:invalid_source_hash" in errors


def test_missing_agent_decisions_file(tmp_path: Path) -> None:
    payload, errors = load_agent_decisions(tmp_path / "missing.json")

    assert payload is None
    assert errors[0].startswith("agent_decisions_missing:")
