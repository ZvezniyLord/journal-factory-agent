from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class PathBoundaryError(RuntimeError):
    """Raised when a path escapes the clean-room workspace."""


@dataclass(frozen=True)
class PathGuard:
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.resolve())

    def inside(self, candidate: str | Path) -> Path:
        path = Path(candidate)
        if not path.is_absolute():
            path = self.root / path
        resolved = path.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise PathBoundaryError(
                f"Path escapes clean-room workspace: {resolved} (root={self.root})"
            ) from exc
        return resolved

    def assert_inside(self, candidate: str | Path) -> None:
        self.inside(candidate)
