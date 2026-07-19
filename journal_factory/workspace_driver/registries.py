from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .models import ReportRecord, WorkspaceLayout


@dataclass(frozen=True, slots=True)
class PathRegistry:
    paths: Mapping[str, Path]

    def __post_init__(self) -> None:
        normalized = dict(self.paths)
        if not all(path.is_absolute() for path in normalized.values()):
            raise ValueError("Path registry values must be absolute")
        object.__setattr__(self, "paths", MappingProxyType(normalized))

    @classmethod
    def from_layout(cls, layout: WorkspaceLayout) -> PathRegistry:
        return cls(layout.paths)

    def to_dict(self) -> dict[str, str]:
        return {name: str(path) for name, path in self.paths.items()}


@dataclass(frozen=True, slots=True)
class ReportRegistry:
    reports: Mapping[str, ReportRecord]

    def __post_init__(self) -> None:
        object.__setattr__(self, "reports", MappingProxyType(dict(self.reports)))

    @classmethod
    def from_layout(cls, layout: WorkspaceLayout) -> ReportRegistry:
        formats = {
            "run_manifest": "json",
            "action_log": "jsonl",
            "path_registry": "json",
            "report_registry": "json",
            "run_summary": "html",
            "dashboard_state": "json",
        }
        reports = {
            name: ReportRecord(
                name=name,
                format=formats[name],
                producer="workspace_driver" if name != "dashboard_state" else "dashboard_core",
                path=path,
                status="pending" if name == "dashboard_state" else "complete",
            )
            for name, path in layout.reports.items()
        }
        return cls(reports)

    def to_dict(self) -> dict[str, dict[str, str]]:
        return {name: report.to_dict() for name, report in self.reports.items()}
