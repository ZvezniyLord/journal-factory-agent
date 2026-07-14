from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_annotation_keyword_exact_spacing():
    s=(ROOT/'skills'/'naukainfo-annotation-keywords-normalization'/'MODULE.md').read_text(encoding='utf-8')
    assert 'zero empty paragraphs' in s
    assert 'exactly one empty paragraph after' in s

def test_nested_shape_caption_contract():
    s=(ROOT/'skills'/'naukainfo-shape-textbox-nested-table-contract'/'MODULE.md').read_text(encoding='utf-8')
    for token in ['w:txbxContent','РисПід','single spacing','zero first-line indent','Compatibility-fallback']:
        assert token in s
