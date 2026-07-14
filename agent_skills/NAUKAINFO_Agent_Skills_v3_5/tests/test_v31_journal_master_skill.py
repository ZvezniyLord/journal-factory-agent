from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_only_one_discoverable_skill():
    skills=sorted((ROOT/'skills').glob('*/SKILL.md'))
    assert len(skills)==1
    assert skills[0].parent.name=='journal'

def test_master_skill_fail_closed_and_project_scoped():
    t=(ROOT/'skills'/'journal'/'SKILL.md').read_text(encoding='utf-8').lower()
    assert 'дирежор' in t
    assert 'лише явно' in t or 'явно активував' in t
    assert 'прізвищ авторів' in t
    assert 'кожної статті' in t
    assert 'deep_text_integrity_audit.py' in t
    assert 'blocked' in t

def test_internal_modules_not_discoverable():
    mods=list((ROOT/'skills').glob('naukainfo-*/MODULE.md'))
    assert len(mods)>=45
    assert not list((ROOT/'skills').glob('naukainfo-*/SKILL.md'))

def test_generic_audit_script_has_no_named_author_branches():
    t=(ROOT/'scripts'/'deep_text_integrity_audit.py').read_text(encoding='utf-8').casefold()
    for name in ['тодорова','магдисюк','гнисюк','novak','sherbon']:
        assert name not in t
