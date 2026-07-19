from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Any

from journal_factory.phase1_app.composition import build_application
from journal_factory.phase1_app.server import Phase1HttpServer


class UnusedDialog:
    def select(self, kind: str) -> str | None:
        raise AssertionError("The real-run API does not open a dialog")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _request(base_url: str, path: str, method: str = "GET", body=None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        base_url + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read())
        if not isinstance(payload, dict):
            raise AssertionError("API response must be an object")
        return payload


def run(source: Path, evidence: Path) -> dict[str, Any]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    evidence.mkdir(parents=True, exist_ok=True)
    output_parent = evidence / "workspace-parent"
    output_parent.mkdir(exist_ok=True)
    source_size = source.stat().st_size
    source_hash_before = _sha256(source)
    root = Path(__file__).resolve().parents[2]
    application = build_application(
        desktop_path=Path.home() / "Desktop",
        state_directory=evidence / "state",
        dialog=UnusedDialog(),
    )
    server = Phase1HttpServer(application, index_path=root / "index.html")
    server.start()
    try:
        request = {
            "source_path": str(source),
            "output_parent": str(output_parent.resolve()),
            "journal_number": "95",
        }
        responses = {
            "defaults": _request(server.base_url, "/api/workspace/defaults"),
            "validation": _request(server.base_url, "/api/workspace/validate", "POST", request),
            "creation": _request(server.base_url, "/api/workspace/create", "POST", request),
        }
        run_id = responses["creation"]["workspace"]["run_id"]
        responses["start"] = _request(
            server.base_url,
            "/api/runs/start",
            "POST",
            {**request, "run_id": run_id},
        )
        responses["refresh"] = _request(server.base_url, f"/api/runs/{run_id}")
        responses["resume"] = _request(server.base_url, f"/api/runs/{run_id}/resume", "POST", {})
        responses["repeat_creation"] = _request(
            server.base_url, "/api/workspace/create", "POST", request
        )
    finally:
        server.stop()

    for name, payload in responses.items():
        (evidence / f"api-{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    workspace = responses["start"]["workspace"]
    reports = {name: Path(path) for name, path in workspace["reports"].items()}
    paths = {name: Path(path) for name, path in workspace["paths"].items()}
    required_reports = {
        "run_manifest",
        "action_log",
        "path_registry",
        "report_registry",
        "run_summary",
        "dashboard_state",
    }
    if set(reports) != required_reports:
        raise AssertionError(f"Unexpected reports: {sorted(reports)}")
    if not all(path.is_absolute() and path.exists() for path in reports.values()):
        raise AssertionError("Every report must exist at an absolute path")
    if not all(path.is_absolute() and path.is_dir() for path in paths.values()):
        raise AssertionError("Every workspace path must be an absolute directory")

    manifest = json.loads(reports["run_manifest"].read_text(encoding="utf-8"))
    path_registry = json.loads(reports["path_registry"].read_text(encoding="utf-8"))
    report_registry = json.loads(reports["report_registry"].read_text(encoding="utf-8"))
    dashboard = json.loads(reports["dashboard_state"].read_text(encoding="utf-8"))
    actions = [
        json.loads(line)
        for line in reports["action_log"].read_text(encoding="utf-8").splitlines()
    ]
    run_id = workspace["run_id"]
    if manifest["run_id"] != run_id or dashboard["run_id"] != run_id:
        raise AssertionError("Run IDs are incoherent")
    if manifest["journal_number"] != "95":
        raise AssertionError("Journal number is incoherent")
    if Path(manifest["source_path"]) != source:
        raise AssertionError("Manifest source path is incoherent")
    if set(path_registry["paths"]) != set(paths):
        raise AssertionError("Path registry is incoherent")
    if set(report_registry["reports"]) != required_reports:
        raise AssertionError("Report registry is incoherent")
    if [item["sequence"] for item in actions] != list(range(1, len(actions) + 1)):
        raise AssertionError("Action sequence is incoherent")
    if responses["repeat_creation"]["workspace"]["run_id"] != run_id:
        raise AssertionError("Repeated creation did not safely restore the run")

    source_hash_after = _sha256(source)
    if source_hash_after != source_hash_before or source.stat().st_size != source_size:
        raise AssertionError("The canonical source archive changed")
    result = {
        "status": "PASS WITH WARNINGS",
        "source_path": str(source),
        "source_size": source_size,
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "run_id": run_id,
        "journal_number": manifest["journal_number"],
        "workspace_path": workspace["workspace_path"],
        "run_state": responses["start"]["run"]["state"],
        "action_count": len(actions),
        "report_paths": {name: str(path) for name, path in reports.items()},
        "output_paths": {name: str(path) for name, path in paths.items()},
        "source_unchanged": True,
        "production_ready": False,
    }
    (evidence / "acceptance-report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(run(arguments.source, arguments.evidence), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
