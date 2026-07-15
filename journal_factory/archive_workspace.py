from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
import hashlib
import json
import shutil
import zipfile


OFFICE_TEMP_PREFIXES = ("~$", "._~$", "._")
SERVICE_DIR_PARTS = {"__MACOSX", ".git", ".svn", ".DS_Store"}
ARTICLE_EXTENSIONS = {".docx", ".doc"}


@dataclass(frozen=True)
class InventoryFile:
    path: str
    size: int
    extension: str
    sha256: str
    article_candidate: bool
    service_file: bool


def prepare_archive_workspace(source: Path, workspace_dir: Path, reports_dir: Path) -> dict:
    workspace_source = workspace_dir / "source"
    if workspace_source.exists():
        shutil.rmtree(workspace_source)
    workspace_source.mkdir(parents=True, exist_ok=True)

    if source.is_file() and source.suffix.lower() == ".zip":
        _extract_zip_safe(source, workspace_source)
        source_type = "zip"
    elif source.is_dir():
        _copy_directory(source, workspace_source)
        source_type = "directory"
    else:
        raise FileNotFoundError(f"Source must be a ZIP file or directory: {source}")

    files = inventory_workspace(workspace_source)
    report = {
        "source": str(source),
        "source_type": source_type,
        "workspace_source": str(workspace_source),
        "file_count": len(files),
        "files": [asdict(item) for item in files],
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "archive_inventory.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def inventory_workspace(workspace_source: Path) -> list[InventoryFile]:
    files: list[InventoryFile] = []
    for path in sorted(item for item in workspace_source.rglob("*") if item.is_file()):
        rel = path.relative_to(workspace_source).as_posix()
        service = is_service_file(rel)
        files.append(
            InventoryFile(
                path=rel,
                size=path.stat().st_size,
                extension=path.suffix.lower(),
                sha256=sha256_file(path),
                article_candidate=is_article_candidate(rel) and not service,
                service_file=service,
            )
        )
    return files


def is_service_file(relative_path: str) -> bool:
    parts = PurePosixPath(relative_path).parts
    if any(part in SERVICE_DIR_PARTS for part in parts):
        return True
    name = parts[-1] if parts else relative_path
    return name.startswith(OFFICE_TEMP_PREFIXES)


def is_article_candidate(relative_path: str) -> bool:
    path = PurePosixPath(relative_path)
    return path.suffix.lower() in ARTICLE_EXTENSIONS and not is_service_file(relative_path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_zip_safe(source: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            member = PurePosixPath(info.filename)
            if info.filename.startswith("/") or ".." in member.parts:
                raise ValueError(f"Blocked unsafe ZIP member: {info.filename}")
            target = (destination / Path(*member.parts)).resolve()
            if not _is_relative_to(target, destination):
                raise ValueError(f"Blocked ZIP member outside workspace: {info.filename}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)


def _copy_directory(source: Path, destination: Path) -> None:
    source = source.resolve()
    for path in source.rglob("*"):
        rel = path.relative_to(source)
        target = destination / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
