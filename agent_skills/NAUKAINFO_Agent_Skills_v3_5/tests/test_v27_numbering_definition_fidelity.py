from pathlib import Path


def test_numbering_skill_documented():
    skill = Path('skills/naukainfo-numbering-definition-fidelity/MODULE.md')
    text = skill.read_text(encoding='utf-8')
    assert 'numFmt=bullet' in text
    assert 'reference lists restart independently at 1' in text
    assert 'No author text may be changed' in text


def test_numbering_script_contains_no_body_text_rewrite():
    script = Path('scripts/audit_numbering_definition_fidelity.py').read_text(encoding='utf-8')
    assert 'It never changes body text' in script
    assert 'numbering.xml' in script
    assert 'numFmt' in script and 'lvlText' in script
