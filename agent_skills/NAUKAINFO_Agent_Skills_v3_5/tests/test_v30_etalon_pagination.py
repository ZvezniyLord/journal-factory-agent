from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_etalon_pagination_skill_contract():
    s=(ROOT/'skills'/'naukainfo-etalon-section-pagination-fidelity'/'MODULE.md').read_text(encoding='utf-8')
    for token in ['three-section','pgNumType','footerReference','TABLE OF CONTENTS','ETALON_SECTION_PAGINATION_BLOCKED']:
        assert token in s

def test_article_boundary_contract_uses_pagebreakbefore():
    s=(ROOT/'skills'/'naukainfo-pagebreak-and-empty-paragraph-policy'/'MODULE.md').read_text(encoding='utf-8')
    assert 'pageBreakBefore' in s
    assert 'Do not create an empty paragraph that contains only a manual page break' in s
