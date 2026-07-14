from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HEADING='SPECIAL THANKS FOR ACTIVE PARTICIPATION IN THE SCIENTIFIC AND PRACTICAL CONFERENCE ARE EXTENDED TO THE FOLLOWING PARTICIPANTS:'

def test_free_listener_toc_contract():
    s=(ROOT/'skills'/'naukainfo-free-listener-toc-section'/'MODULE.md').read_text(encoding='utf-8')
    for token in [HEADING,'TabSEC','TabPIP','comma + space','exactly one following three-cell row','no page number']:
        assert token in s
    assert 'Add one author row per listener' not in s

def test_toc_builder_invokes_listener_skill():
    s=(ROOT/'skills'/'naukainfo-toc-table-builder'/'MODULE.md').read_text(encoding='utf-8')
    assert 'naukainfo-free-listener-toc-section' in s
    assert HEADING in s
