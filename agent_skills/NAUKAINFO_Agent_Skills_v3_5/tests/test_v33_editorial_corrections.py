from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_master_skill_contains_exact_listener_layout():
    s=(ROOT/'skills'/'journal'/'SKILL.md').read_text(encoding='utf-8')
    assert 'SPECIAL THANKS FOR ACTIVE PARTICIPATION IN THE SCIENTIFIC AND PRACTICAL CONFERENCE ARE EXTENDED TO THE FOLLOWING PARTICIPANTS:' in s
    assert 'actual style `TabPIP`' in s
    assert 'через `, `' in s
    assert 'one row per listener' not in s

def test_author_udc_and_table_caption_rules_are_explicit():
    master=(ROOT/'skills'/'journal'/'SKILL.md').read_text(encoding='utf-8')
    author=(ROOT/'skills'/'naukainfo-author-header-cleanup'/'MODULE.md').read_text(encoding='utf-8')
    table=(ROOT/'skills'/'naukainfo-table-figure-caption-contract'/'MODULE.md').read_text(encoding='utf-8')
    assert 'рівно один службовий blank після фактичного UDC' in master
    assert 'must not end in `,`, `;`, or `:`' in author
    assert 'actual ETALON `РисПід` style (`styleId af6`)' in table
    assert '`Normal` plus direct formatting is not accepted' in table

def test_reference_pipeline_is_frozen_after_pass():
    s=(ROOT/'skills'/'journal'/'SKILL.md').read_text(encoding='utf-8')
    assert 'validated references freeze' in s
