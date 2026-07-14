from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_v17_business_rules_present():
    text = (ROOT / 'docs' / 'BUSINESS_RULES.md').read_text(encoding='utf-8')
    assert 'Після назви статті' in text
    assert 'Після кожної таблиці' in text
    assert 'після `Джерело`' in text
    assert 'Після штампа `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`' in text
    assert '`pip` не є заголовком' in text
    assert 'Ctrl+Space' in text

def test_skill_exists():
    skill = ROOT / 'skills' / 'naukainfo-spacing-toc-contract' / 'MODULE.md'
    assert skill.exists()
    data = skill.read_text(encoding='utf-8')
    assert 'after each article title' in data
    assert 'Only these roles may have outline levels' in data
    assert 'pip' in data
