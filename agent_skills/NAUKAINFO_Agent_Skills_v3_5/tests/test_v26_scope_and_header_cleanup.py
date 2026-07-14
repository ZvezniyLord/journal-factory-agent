from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

def test_scope_guard_mentions_activation_only_current_project():
    txt = (BASE / "docs" / "PROJECT_SCOPE.md").read_text(encoding="utf-8")
    assert "Дирежор" in txt
    assert "NAUKAINFO Journal Builder" in txt
    assert "актив" in txt.lower()
    assert "звичайних чатах" in txt.lower()


def test_author_header_cleanup_mentions_damaged_email_fragments_and_section_notes():
    txt = (BASE / "skills" / "naukainfo-author-header-cleanup" / "MODULE.md").read_text(encoding="utf-8")
    assert "Секція 013" in txt
    assert "nv/" in txt
    assert "AUTOR" in txt and "pip" in txt


def test_frontmatter_order_skill_has_canonical_order():
    txt = (BASE / "skills" / "naukainfo-front-matter-order-and-title-dedupe" / "MODULE.md").read_text(encoding="utf-8")
    assert "DOI/UDC → author header → article title" in txt
    assert "Анотація" in txt or "annotation" in txt.lower()
