from pathlib import Path

import pytest

from astra_journal.path_guard import PathBoundaryError, PathGuard


def test_inside_accepts_relative_path(tmp_path: Path) -> None:
    guard = PathGuard(tmp_path)
    resolved = guard.inside("runs/bootstrap")
    assert resolved == (tmp_path / "runs" / "bootstrap").resolve()


def test_inside_rejects_parent_escape(tmp_path: Path) -> None:
    guard = PathGuard(tmp_path)
    with pytest.raises(PathBoundaryError):
        guard.inside("../legacy")
