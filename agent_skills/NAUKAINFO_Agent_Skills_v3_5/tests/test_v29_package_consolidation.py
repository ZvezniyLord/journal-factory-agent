from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_no_loose_skill_markdown_files():
    assert not list((ROOT/'skills').glob('*.md'))

def test_every_skill_is_canonical_directory():
    dirs=[p for p in (ROOT/'skills').iterdir() if p.is_dir()]
    assert dirs
    assert all((p/'MODULE.md').exists() for p in dirs if p.name.startswith('naukainfo-'))

def test_new_scripts_present():
    for name in ['recover_legacy_doc_images.py','audit_media_content_hashes.py','audit_toc_author_sync.py','normalize_multilingual_markers.py']:
        assert (ROOT/'scripts'/name).exists()

def test_backup_policy_documented():
    text=(ROOT/'skills'/'naukainfo-versioned-backup-release'/'MODULE.md').read_text(encoding='utf-8')
    assert 'Never overwrite' in text
    assert 'prior skills ZIP' in text
