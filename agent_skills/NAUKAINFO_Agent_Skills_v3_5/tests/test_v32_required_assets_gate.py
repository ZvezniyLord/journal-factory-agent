from pathlib import Path
from zipfile import ZipFile

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "journal" / "SKILL.md"
SCRIPT = ROOT / "scripts" / "preflight_required_assets.py"


def test_master_skill_blocks_missing_templates():
    text = SKILL.read_text(encoding="utf-8")
    assert "BUILD BLOCKED: REQUIRED_ASSET_MISSING" in text
    assert "Заборонено створювати" in text
    assert "ETALON-JOURNAL.docx" in text
    assert "Jurnal.dotx" in text


def test_preflight_script_has_required_style_ids():
    text = SCRIPT.read_text(encoding="utf-8")
    for style_id in ["SECTION", "AUTOR", "TabSEC", "TabPIP", "TabTaitl", "REFER", "ad", "af6"]:
        assert f'"{style_id}"' in text


def test_only_one_discoverable_skill():
    skill_files = list((ROOT / "skills").glob("*/SKILL.md"))
    assert skill_files == [SKILL]
