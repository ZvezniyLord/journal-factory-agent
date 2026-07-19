from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .models import DashboardSnapshot
from .ports import DashboardPortError


class JsonDashboardStateStore:
    """Atomic JSON storage for Dashboard projections at a supplied location."""

    def __init__(
        self,
        state_directory: str | Path,
        *,
        replace_file: Callable[[Path, Path], None] = os.replace,
    ) -> None:
        self._state_directory = Path(state_directory).expanduser().resolve()
        self._replace_file = replace_file

    def state_path(self, run_id: str) -> Path:
        if not isinstance(run_id, str) or not run_id.strip():
            raise DashboardPortError(
                code="DASHBOARD_STATE_INVALID",
                message="Dashboard run ID must be non-empty.",
                retryable=False,
            )
        digest = hashlib.sha256(run_id.encode("utf-8")).hexdigest()
        return self._state_directory / f"{digest}.json"

    def save(self, snapshot: DashboardSnapshot) -> None:
        destination = self.state_path(snapshot.run_id)
        temporary_path: Path | None = None
        try:
            self._state_directory.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(
                snapshot.to_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ) + "\n"
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self._state_directory,
                prefix=f".{destination.stem}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            self._replace_file(temporary_path, destination)
        except DashboardPortError:
            raise
        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise DashboardPortError(
                code="DASHBOARD_STATE_PERSISTENCE_FAILED",
                message="Dashboard state could not be persisted.",
                retryable=True,
            ) from None

    def load(self, run_id: str) -> DashboardSnapshot | None:
        source = self.state_path(run_id)
        if not source.exists():
            return None
        try:
            payload: Any = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("dashboard state must be an object")
            snapshot = DashboardSnapshot.from_dict(payload)
            if snapshot.run_id != run_id:
                raise ValueError("dashboard run ID does not match")
            return snapshot
        except DashboardPortError:
            raise
        except Exception:
            raise DashboardPortError(
                code="DASHBOARD_STATE_INVALID",
                message="Persisted dashboard state is invalid.",
                retryable=False,
            ) from None
