from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_v22_toc_skill_exists():
    t=(ROOT/'skills/naukainfo-toc-table-builder/MODULE.md').read_text(encoding='utf-8')
    assert 'three physical columns' in t
    assert 'Tab_SEC' in t and 'Tab_PIP' in t and 'Tab_Taitl' in t
    assert 'loose paragraphs' in t

def test_v22_frontmatter_skill_exists():
    t=(ROOT/'skills/naukainfo-front-matter-order-and-title-dedupe/MODULE.md').read_text(encoding='utf-8')
    assert 'canonical order' in t.lower()
    assert 'Duplicate-title prevention' in t
    assert 'Exactly one blank paragraph' in t

def test_v22_business_docs_updated():
    t=(ROOT/'docs/JOURNAL_CONTRACT.md').read_text(encoding='utf-8')
    assert 'v2.2 TOC/front-matter update' in t
    assert 'Page numbering from ETALON' in t
