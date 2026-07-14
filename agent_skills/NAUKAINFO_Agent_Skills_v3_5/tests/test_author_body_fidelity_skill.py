from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "naukainfo-author-body-fidelity" / "MODULE.md"
AGENT = ROOT / "AGENT.md"
BUSINESS = ROOT / "docs" / "BUSINESS_RULES.md"
MAP = ROOT / "docs" / "SKILL_MAP.md"


def test_priority_skill_exists_and_is_fail_closed():
    text = SKILL.read_text(encoding="utf-8")
    assert 'priority: "0-critical"' in text
    assert "100% lexical preservation" in text
    assert "at least 99% structural preservation" in text
    assert "manual body list" in text.lower()
    assert "fail" in text.lower()


def test_orchestrator_places_body_fidelity_first():
    text = AGENT.read_text(encoding="utf-8")
    assert "naukainfo-author-body-fidelity" in text
    assert "найвищ" in text.lower()


def test_business_contract_and_map_reference_priority_skill():
    assert "99%" in BUSINESS.read_text(encoding="utf-8")
    map_text = MAP.read_text(encoding="utf-8")
    assert "Priority 0" in map_text
    assert "naukainfo-author-body-fidelity" in map_text
