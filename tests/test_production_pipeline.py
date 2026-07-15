import json
from pathlib import Path

from jsonschema import Draft202012Validator

from journal_factory.config import AppConfig
from journal_factory.production_pipeline import run_production_build
from journal_factory.preflight import MANDATORY_SOURCE_PACK_FILES
from journal_factory.skills_loader import REQUIRED_MODULES


def _write_source_pack(root: Path) -> None:
    root.mkdir()
    for rel in MANDATORY_SOURCE_PACK_FILES:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("required", encoding="utf-8")
    tests_dir = root / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_quality_gate.py").write_text("def test_placeholder(): pass\n", encoding="utf-8")


def _write_valid_skill(root: Path) -> None:
    journal = root / "skills" / "journal"
    journal.mkdir(parents=True)
    journal.joinpath("SKILL.md").write_text(
        "---\nname: journal\nmetadata:\n  version: \"3.5.0\"\n---\n# Journal\n",
        encoding="utf-8",
    )
    for name in REQUIRED_MODULES:
        module_dir = root / "skills" / name
        module_dir.mkdir(parents=True)
        module_dir.joinpath("MODULE.md").write_text(
            f"---\nname: {name}\nmetadata:\n  version: \"1.0.0\"\n---\n# Module\n",
            encoding="utf-8",
        )


def test_production_pipeline_reaches_frontmatter_after_valid_manifest_and_snapshots(tmp_path: Path, monkeypatch) -> None:
    source = Path("fixtures/manifest")
    etalon = tmp_path / "ETALON-JOURNAL.docx"
    template = tmp_path / "Jurnal.dotx"
    source_pack = tmp_path / "source_pack"
    etalon.write_bytes(b"placeholder")
    template.write_bytes(b"placeholder")
    _write_source_pack(source_pack)
    skill_root = tmp_path / "skills_root"
    _write_valid_skill(skill_root)
    monkeypatch.setenv("AGENT_SKILLS_ROOT", str(skill_root))

    config = AppConfig(
        mode="production",
        archive=source,
        etalon=etalon,
        template=template,
        source_pack=source_pack,
        build_dir=tmp_path / "build" / "production",
        reports_dir=tmp_path / "build" / "production" / "reports",
    )

    result = run_production_build(config)
    gate = json.loads((config.reports_dir / "final_quality_gate.json").read_text(encoding="utf-8"))
    manifest = json.loads((config.reports_dir / "active_skill_manifest.json").read_text(encoding="utf-8"))
    schema = json.loads(Path("schemas/active-skill-manifest.schema.json").read_text(encoding="utf-8"))

    assert result["status"] == "BUILD BLOCKED"
    assert gate["production_ready"] is False
    assert gate["skill_registry_status"] == "PASS"
    assert gate["manifest_status"] == "PASS"
    assert gate["source_snapshot_status"] == "PASS"
    assert "NEXT_PHASE_FRONTMATTER_NOT_IMPLEMENTED" in gate["critical"]
    Draft202012Validator(schema).validate(manifest)


def test_production_pipeline_blocks_invalid_agent_decisions(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    etalon = tmp_path / "ETALON-JOURNAL.docx"
    template = tmp_path / "Jurnal.dotx"
    source_pack = tmp_path / "source_pack"
    etalon.write_bytes(b"placeholder")
    template.write_bytes(b"placeholder")
    _write_source_pack(source_pack)
    skill_root = tmp_path / "skills_root"
    _write_valid_skill(skill_root)
    monkeypatch.setenv("AGENT_SKILLS_ROOT", str(skill_root))
    decisions = tmp_path / "agent_decisions.json"
    decisions.write_text('{"decisions":[{"decision_type":"invalid"}]}', encoding="utf-8")

    config = AppConfig(
        mode="production",
        archive=source,
        etalon=etalon,
        template=template,
        source_pack=source_pack,
        build_dir=tmp_path / "build" / "production",
        reports_dir=tmp_path / "build" / "production" / "reports",
    )

    run_production_build(config, decisions)
    gate = json.loads((config.reports_dir / "final_quality_gate.json").read_text(encoding="utf-8"))

    assert "AGENT_DECISIONS_INVALID" in gate["critical"]
    assert gate["agent_decisions_errors"]
