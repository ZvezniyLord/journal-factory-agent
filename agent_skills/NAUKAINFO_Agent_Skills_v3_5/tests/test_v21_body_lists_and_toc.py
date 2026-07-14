from pathlib import Path

def test_v21_skill_notes_present():
    root = Path(__file__).resolve().parents[1]
    assert (root/'skills/naukainfo-skill-map-change-log/MODULE.md').exists()
    assert 'body lists are author structure' in (root/'skills/naukainfo-author-body-fidelity/MODULE.md').read_text(encoding='utf-8').lower()
    assert 'static toc page numbers' in (root/'skills/naukainfo-multi-article-assembly/MODULE.md').read_text(encoding='utf-8').lower()
