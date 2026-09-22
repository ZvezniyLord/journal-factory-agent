from __future__ import annotations

from pathlib import Path, PurePosixPath
from zipfile import ZipFile


class UnsafeArchivePath(RuntimeError):
    pass


def validate_member_name(name: str) -> PurePosixPath:
    member = PurePosixPath(name)
    if member.is_absolute():
        raise UnsafeArchivePath(f"Absolute archive member is forbidden: {name}")
    if any(part == ".." for part in member.parts):
        raise UnsafeArchivePath(f"Parent traversal archive member is forbidden: {name}")
    return member


def safe_extract_zip(zip_path: str | Path, target_dir: str | Path) -> list[Path]:
    target = Path(target_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []

    with ZipFile(zip_path) as archive:
        for info in archive.infolist():
            member = validate_member_name(info.filename)
            destination = (target / Path(*member.parts)).resolve()
            try:
                destination.relative_to(target)
            except ValueError as exc:
                raise UnsafeArchivePath(
                    f"Archive member escapes extraction root: {info.filename}"
                ) from exc

            if info.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue

            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, destination.open("wb") as sink:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(chunk)
            extracted.append(destination)

    return extracted
