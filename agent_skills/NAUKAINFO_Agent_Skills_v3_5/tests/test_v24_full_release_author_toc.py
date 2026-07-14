from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_toc_author_cleaning_skill_exists_and_forbids_role_leakage():
    text = read('skills/naukainfo-toc-author-cleaning/MODULE.md')
    assert 'only participant names' in text
    assert 'must not include' in text
    assert 'Senior Lecturer' in text
    assert 'імені Івана Огієнка' in text
    assert 'TOC author display uses a cleaned author map' in text


def test_toc_table_builder_mentions_excluding_toc_page_occurrences():
    text = read('skills/naukainfo-toc-table-builder/MODULE.md')
    assert 'section merged row' in text or 'merged row' in text
    assert 'two article rows' in text or 'exactly two rows' in text
    assert 'TOC page occurrences' in text or 'exclude TOC' in text
