from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class LocalFileSystemAdapter:
    def resolve(self, path: str | Path) -> Path:
        return Path(path).expanduser().resolve()

    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def is_directory(self, path: Path) -> bool:
        return path.is_dir()

    def make_directory(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        self.make_directory(path.parent)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink(missing_ok=True)

    def append_text(self, path: Path, content: str) -> None:
        self.make_directory(path.parent)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
