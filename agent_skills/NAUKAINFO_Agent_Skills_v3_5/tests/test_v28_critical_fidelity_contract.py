from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ALL = (ROOT/'docs'/'V2_8_CRITICAL_BLOCKER_REPORT.md').read_text(encoding='utf-8') + "\n" + (ROOT/'docs'/'BUSINESS_RULES.md').read_text(encoding='utf-8')

def test_media_fidelity_gate_mentions_lost_figures():
    text = (ROOT/'skills'/'naukainfo-media-object-fidelity-gate'/'MODULE.md').read_text(encoding='utf-8')
    assert 'Figure 2' in text and 'MEDIA_FIDELITY_BLOCKED' in text

def test_nested_shape_table_skill_recurses_txbxcontent():
    text = (ROOT/'skills'/'naukainfo-shape-textbox-nested-table-contract'/'MODULE.md').read_text(encoding='utf-8')
    assert 'w:txbxContent' in text and 'nested tables' in text.lower()

def test_reference_language_english_references():
    text = (ROOT/'skills'/'naukainfo-reference-language-and-marker-contract'/'MODULE.md').read_text(encoding='utf-8')
    assert 'REFERENCES' in text and 'СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ' in text

def test_pagebreak_policy_keywords_blank():
    text = (ROOT/'skills'/'naukainfo-pagebreak-and-empty-paragraph-policy'/'MODULE.md').read_text(encoding='utf-8')
    assert 'after keywords' in text and 'article page break' in text
