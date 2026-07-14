from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_v23_toc_skill_pdf_geometry():
    t = (ROOT/'skills/naukainfo-toc-table-builder/MODULE.md').read_text(encoding='utf-8')
    assert 'two rows' in t
    assert 'merged row' in t
    assert '[600, 8300, 739]' in t
    assert 'title in the same row as the author' in t
    assert 'TabSEC' in t and 'TabPIP' in t and 'TabTaitl' in t


def test_v23_toc_script_exists():
    s = (ROOT/'scripts/rebuild_toc_pdf_contract.py').read_text(encoding='utf-8')
    assert 'DEFAULT_GRID_TWIPS = [600, 8300, 739]' in s
    assert 'merge' in s
    assert 'row A' in s or 'author row' in s


def test_v23_changelog_records_failure():
    c = (ROOT/'CHANGELOG.md').read_text(encoding='utf-8')
    assert 'v2.3' in c
    assert 'equal columns' in c.lower()
