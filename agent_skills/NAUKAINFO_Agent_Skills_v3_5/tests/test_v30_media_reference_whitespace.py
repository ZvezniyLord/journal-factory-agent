from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_per_article_media_regressions():
    s=(ROOT/'skills'/'naukainfo-media-object-fidelity-gate'/'MODULE.md').read_text(encoding='utf-8')
    assert 'Magdysiuk Figure 2' in s
    assert 'Todorova Figure 2' in s
    assert 'hard release blocker' in s

def test_unmarked_reference_inference_is_conservative():
    s=(ROOT/'skills'/'naukainfo-reference-block-fidelity'/'MODULE.md').read_text(encoding='utf-8')
    for token in ['unmarked terminal bibliography inference','strong signals','operator review']:
        assert token in s

def test_leading_space_cleanup_is_lexically_safe():
    s=(ROOT/'skills'/'naukainfo-body-leading-space-normalization'/'MODULE.md').read_text(encoding='utf-8')
    assert 'leading spaces' in s and 'non-whitespace character' in s
