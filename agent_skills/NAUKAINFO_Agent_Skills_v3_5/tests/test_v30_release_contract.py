from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_v30_scripts_and_report_present():
    for name in ['finalize_journal_v32.py','repair_journal_v31.py','fix_v31_reference_languages.py']:
        assert (ROOT/'scripts'/name).exists()
    assert (ROOT/'docs'/'V3_0_VERIFIED_RELEASE_REPORT.md').exists()

def test_readme_version_and_scope():
    s=(ROOT/'README.md').read_text(encoding='utf-8')
    assert s.startswith('# NAUKAINFO Agent Skills v3.5')
    assert 'Дирежор' in s and '96 rendered pages' in s
