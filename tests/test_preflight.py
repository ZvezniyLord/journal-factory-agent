from pathlib import Path

from journal_factory.config import AppConfig
from journal_factory.preflight import run_preflight


def test_preflight_blocks_missing_mandatory_files(tmp_path: Path) -> None:
    config = AppConfig(
        mode="diagnostic-mvp",
        archive=tmp_path / "missing.zip",
        etalon=tmp_path / "missing.docx",
        template=tmp_path / "missing.dotx",
        source_pack=tmp_path / "missing_pack",
        build_dir=tmp_path / "build",
        reports_dir=tmp_path / "build" / "reports",
    )
    result = run_preflight(config)
    assert result["status"] == "BUILD BLOCKED"
    assert {b["name"] for b in result["blockers"]} >= {"archive", "etalon", "template", "source_pack"}
