import json
from pathlib import Path

from journal_factory.config import AppConfig
from journal_factory.production_pipeline import run_production_build


def test_production_pipeline_blocks_until_implemented(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    etalon = tmp_path / "ETALON-JOURNAL.docx"
    template = tmp_path / "Jurnal.dotx"
    source_pack = tmp_path / "source_pack"
    etalon.write_bytes(b"placeholder")
    template.write_bytes(b"placeholder")
    source_pack.mkdir()

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

    assert result["status"] == "BUILD BLOCKED"
    assert gate["production_ready"] is False
    assert "PRODUCTION_PIPELINE_NOT_IMPLEMENTED" in gate["critical"]
