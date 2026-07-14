from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_new_skills_and_removed_failed_rules():
    business=(ROOT/'docs'/'BUSINESS_RULES.md').read_text(encoding='utf-8')
    assert '`Анотація.`' in business and '`Ключові слова:`' in business
    assert '`URL: `' in business and '`DOI: `' in business
    assert 'REFERENCE_BOUNDARIES_AMBIGUOUS' in business
    assert 'нульовий відступ для annotation/keywords' in business
    for name in ['naukainfo-annotation-keywords-normalization','naukainfo-author-header-cleanup','naukainfo-reference-entry-reconstruction']:
        assert (ROOT/'skills'/name/'MODULE.md').exists()

def test_reference_skill_requires_blank_after_stamp():
    text=(ROOT/'skills'/'naukainfo-reference-block-fidelity'/'MODULE.md').read_text(encoding='utf-8')
    assert 'Exactly one empty paragraph between the stamp and reference entry 1.' in text
