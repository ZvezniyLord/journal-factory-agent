from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ProductionRunRequest:
    archive_path: str
    output_root: str | None = None
    template_path: str | None = None
    conference_number: str | None = None
    allow_overwrite: bool = False


def load_request(path: str | Path) -> ProductionRunRequest:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return ProductionRunRequest(**payload)


def save_request(path: str | Path, request: ProductionRunRequest) -> None:
    Path(path).write_text(
        json.dumps(asdict(request), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def resolve_final_destination(
    *,
    output_root: str | Path,
    conference_number: str,
    filename_pattern: str = "{conference_number}-final.docx",
    overwrite: bool = False,
) -> Path:
    root = Path(output_root)
    conference_dir = root / str(conference_number)
    conference_dir.mkdir(parents=True, exist_ok=True)

    filename = filename_pattern.format(conference_number=conference_number)
    destination = conference_dir / filename
    if destination.exists() and not overwrite:
        stem, suffix = destination.stem, destination.suffix
        index = 2
        while True:
            candidate = conference_dir / f"{stem}-v{index}{suffix}"
            if not candidate.exists():
                return candidate
            index += 1
    return destination
