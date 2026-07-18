from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

from .corpus_utils import is_relative_to

RAR4 = b"Rar!\x1a\x07\x00"
RAR5 = b"Rar!\x1a\x07\x01\x00"
ZIP_MAGICS = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")


class ArchiveValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ArchiveEntry:
    path: str
    size: int | None = None
    packed_size: int | None = None
    attributes: str | None = None
    is_directory: bool = False
    is_link: bool = False


@dataclass(frozen=True)
class ArchiveLimits:
    max_files: int = 200_000
    max_uncompressed_bytes: int = 100 * 1024**3
    max_ratio: float = 200.0
    max_path_length: int = 1024
    max_depth: int = 30
    max_single_file_bytes: int = 10 * 1024**3


def detect_rar(path: Path) -> str:
    with path.open("rb") as stream:
        head = stream.read(8)
    if head.startswith(RAR5):
        return "RAR5"
    if head.startswith(RAR4):
        return "RAR4"
    raise ArchiveValidationError("INVALID_RAR_SIGNATURE")


def detect_archive(path: Path) -> str:
    with path.open("rb") as stream:
        head = stream.read(8)
    if head.startswith(RAR5):
        return "RAR5"
    if head.startswith(RAR4):
        return "RAR4"
    if any(head.startswith(magic) for magic in ZIP_MAGICS):
        return "ZIP"
    raise ArchiveValidationError("UNSUPPORTED_ARCHIVE_SIGNATURE")


def _rar_tool() -> tuple[str, list[str]]:
    for binary in ("7zz", "7z"):
        if shutil.which(binary):
            return binary, ["l", "-slt"]
    if shutil.which("unrar"):
        return "unrar", ["lt"]
    raise ArchiveValidationError("RAR_TOOL_UNAVAILABLE")


def _zip_entries(path: Path) -> list[ArchiveEntry]:
    try:
        with zipfile.ZipFile(path) as archive:
            rows = []
            for info in archive.infolist():
                unix_mode = (info.external_attr >> 16) & 0xFFFF
                is_link = stat.S_ISLNK(unix_mode)
                rows.append(ArchiveEntry(
                    path=info.filename,
                    size=info.file_size,
                    packed_size=info.compress_size,
                    attributes=oct(unix_mode),
                    is_directory=info.is_dir(),
                    is_link=is_link,
                ))
            return rows
    except zipfile.BadZipFile as exc:
        raise ArchiveValidationError(f"ZIP_LIST_FAILED:{exc}") from exc


def list_entries(path: Path) -> list[ArchiveEntry]:
    return list_archive_entries(path, detect_rar(path))


def list_archive_entries(path: Path, archive_format: str | None = None) -> list[ArchiveEntry]:
    archive_format = archive_format or detect_archive(path)
    if archive_format == "ZIP":
        return _zip_entries(path)
    binary, args = _rar_tool()
    proc = subprocess.run(
        [binary, *args, str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
        check=False,
    )
    if proc.returncode != 0:
        raise ArchiveValidationError(f"RAR_LIST_FAILED:{proc.returncode}:{proc.stderr[-500:]}")
    if binary.startswith("7z"):
        return _parse_7z_slt(proc.stdout, archive_name=path.name)
    return _parse_unrar_lt(proc.stdout)


def _parse_7z_slt(text: str, archive_name: str) -> list[ArchiveEntry]:
    blocks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            if current:
                blocks.append(current)
                current = {}
            continue
        if " = " in line:
            key, value = line.split(" = ", 1)
            current[key.strip()] = value.strip()
    if current:
        blocks.append(current)
    out = []
    for block in blocks:
        path = block.get("Path")
        if not path or path == archive_name or "Type" in block:
            continue
        attr = block.get("Attributes", "")
        is_dir = block.get("Folder") == "+" or attr.startswith("D")
        is_link = bool(block.get("Symbolic Link") or block.get("Hard Link")) or " L" in f" {attr} "

        def integer(name: str) -> int | None:
            try:
                return int(block[name])
            except (KeyError, ValueError):
                return None

        out.append(ArchiveEntry(path, integer("Size"), integer("Packed Size"), attr, is_dir, is_link))
    return out


def _parse_unrar_lt(text: str) -> list[ArchiveEntry]:
    out = []
    for line in text.splitlines():
        match = re.match(r"^\s*Name:\s*(.+)$", line)
        if match:
            out.append(ArchiveEntry(match.group(1).strip()))
    if not out:
        raise ArchiveValidationError("UNRAR_LIST_UNPARSEABLE")
    return out


def _validate_relative_path(raw_path: str, limits: ArchiveLimits) -> PurePosixPath:
    raw = raw_path.replace("\\", "/")
    if "\x00" in raw or len(raw) > limits.max_path_length:
        raise ArchiveValidationError("UNSAFE_ARCHIVE_PATH")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("..", "") for part in path.parts) or re.match(r"^[A-Za-z]:", raw):
        raise ArchiveValidationError(f"PATH_TRAVERSAL:{raw}")
    if len(path.parts) > limits.max_depth:
        raise ArchiveValidationError("ARCHIVE_NESTING_LIMIT")
    return path


def validate_entries(entries: Iterable[ArchiveEntry], archive_size: int, limits: ArchiveLimits = ArchiveLimits()) -> dict:
    entries = list(entries)
    if len(entries) > limits.max_files:
        raise ArchiveValidationError("ARCHIVE_FILE_COUNT_LIMIT")
    total = 0
    seen: set[str] = set()
    duplicates: list[str] = []
    for entry in entries:
        path = _validate_relative_path(entry.path, limits)
        normalized = str(path).casefold()
        if normalized in seen:
            duplicates.append(entry.path)
        seen.add(normalized)
        if entry.is_link:
            raise ArchiveValidationError(f"ARCHIVE_LINK_REJECTED:{entry.path}")
        size = max(entry.size or 0, 0)
        if size > limits.max_single_file_bytes:
            raise ArchiveValidationError(f"ARCHIVE_SINGLE_FILE_LIMIT:{entry.path}")
        total += size
    if duplicates:
        raise ArchiveValidationError(f"ARCHIVE_DUPLICATE_PATHS:{duplicates[:5]}")
    if total > limits.max_uncompressed_bytes:
        raise ArchiveValidationError("ARCHIVE_UNCOMPRESSED_LIMIT")
    ratio = total / max(archive_size, 1)
    if ratio > limits.max_ratio:
        raise ArchiveValidationError("ARCHIVE_BOMB_RATIO")
    return {"entry_count": len(entries), "total_uncompressed_bytes": total, "expansion_ratio": ratio}


def _extract_zip(path: Path, destination: Path) -> None:
    root = destination.resolve()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            relative = _validate_relative_path(info.filename, ArchiveLimits())
            target = (destination / Path(*relative.parts)).resolve()
            if not is_relative_to(target, root):
                raise ArchiveValidationError(f"EXTRACT_ESCAPE:{info.filename}")
            unix_mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(unix_mode):
                raise ArchiveValidationError(f"EXTRACTED_SYMLINK:{info.filename}")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)


def extract_readonly(path: Path, destination: Path) -> None:
    extract_archive_readonly(path, destination, detect_rar(path))


def extract_archive_readonly(path: Path, destination: Path, archive_format: str | None = None) -> None:
    archive_format = archive_format or detect_archive(path)
    destination.mkdir(parents=True, exist_ok=False)
    if archive_format == "ZIP":
        _extract_zip(path, destination)
    else:
        binary, _ = _rar_tool()
        command = [binary, "x", "-y", "-bd", "-bb0", f"-o{destination}", str(path)] if binary.startswith("7z") else [binary, "x", "-o+", "-idq", str(path), str(destination) + os.sep]
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=7200, check=False)
        if proc.returncode != 0:
            raise ArchiveValidationError(f"RAR_EXTRACT_FAILED:{proc.returncode}:{proc.stderr[-500:]}")
    root = destination.resolve()
    for item in destination.rglob("*"):
        if item.is_symlink():
            raise ArchiveValidationError(f"EXTRACTED_SYMLINK:{item}")
        if not is_relative_to(item.resolve(), root):
            raise ArchiveValidationError(f"EXTRACT_ESCAPE:{item}")
