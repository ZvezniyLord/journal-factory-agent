from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


ROOT = Path.cwd()
VALID_MODES = {"diagnostic-mvp", "production", "production-preview"}


@dataclass(frozen=True)
class AppConfig:
    mode: str
    archive: Path
    etalon: Path
    template: Path
    source_pack: Path
    build_dir: Path
    reports_dir: Path


def default_config(archive: str | None = None, mode: str | None = None) -> AppConfig:
    resolved_mode = mode or os.environ.get("JOURNAL_MODE", "diagnostic-mvp")
    if resolved_mode not in VALID_MODES:
        raise ValueError(f"Unsupported journal mode: {resolved_mode}")

    build_root = Path(os.environ.get("JOURNAL_OUTPUT_DIR", str(ROOT / "build")))
    build_dir = build_root / resolved_mode
    return AppConfig(
        mode=resolved_mode,
        archive=Path(archive or os.environ.get("JOURNAL_ARCHIVE", r"N:\Конференції\136")),
        etalon=Path(os.environ.get("JOURNAL_ETALON", r"C:\Users\Vint\Desktop\ETALON-JOURNAL.docx")),
        template=Path(os.environ.get("JOURNAL_TEMPLATE", r"C:\Users\Vint\Desktop\Jurnal.dotx")),
        source_pack=Path(
            os.environ.get(
                "JOURNAL_SOURCE_PACK",
                r"C:\Users\Vint\Downloads\_source_zip\NAukaInfo_JournalBuilder_CLEAN_FOR_CODEX",
            )
        ),
        build_dir=build_dir,
        reports_dir=build_dir / "reports",
    )


def ensure_dirs(config: AppConfig) -> None:
    config.build_dir.mkdir(parents=True, exist_ok=True)
    config.reports_dir.mkdir(parents=True, exist_ok=True)
