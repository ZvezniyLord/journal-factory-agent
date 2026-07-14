from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_business_rules_include_v29_contract():
    s=(ROOT/'docs'/'BUSINESS_RULES.md').read_text(encoding='utf-8')
    for token in ['Legacy DOC conversion','`РИС`','`РисПід`','`REFERENCES`','TOC author rows']:
        assert token in s

def test_skill_map_has_priority_order():
    s=(ROOT/'docs'/'SKILL_MAP.md').read_text(encoding='utf-8')
    assert 'Priority 0' in s and 'Priority 1' in s and 'Priority 2' in s and 'Priority 3' in s
    assert 'naukainfo-legacy-doc-image-recovery' in s
    assert 'naukainfo-toc-body-author-sync' in s
