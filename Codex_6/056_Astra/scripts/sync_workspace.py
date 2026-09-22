from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


REPO = "ZvezniyLord/journal-factory-agent"
BRANCH = "astra/056-clean-room-skeleton"
SOURCE_SUFFIX = Path("Codex_6") / "056_Astra"
PRESERVE = {".venv", "runs", "output"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _locate_source(extract_root: Path) -> Path:
    for marker in extract_root.rglob("ASTRA_MASTER.md"):
        candidate = marker.parent
        try:
            rel = candidate.relative_to(extract_root)
        except ValueError:
            continue
        if tuple(rel.parts[-2:]) == ("Codex_6", "056_Astra"):
            return candidate
    raise RuntimeError("Could not locate Codex_6/056_Astra in downloaded archive")


def sync_workspace(target: Path, *, repo: str = REPO, branch: str = BRANCH) -> dict:
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)

    url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
    with tempfile.TemporaryDirectory(prefix="astra-sync-") as td:
        tmp = Path(td)
        archive = tmp / "repo.zip"
        extract = tmp / "extract"
        extract.mkdir()

        urllib.request.urlretrieve(url, archive)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract)

        source = _locate_source(extract)
        copied = []
        for item in source.iterdir():
            if item.name in PRESERVE:
                continue
            dest = target / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
            copied.append(item.name)

    bootstrap = target / "runs" / "bootstrap"
    bootstrap.mkdir(parents=True, exist_ok=True)
    state = {
        "status": "PASS",
        "source_repository": repo,
        "source_branch": branch,
        "source_path": str(SOURCE_SUFFIX).replace("\\", "/"),
        "local_target": str(target),
        "preserved": sorted(PRESERVE),
        "copied_top_level": sorted(copied),
        "timestamp_utc": _utc_now(),
    }
    (bootstrap / "sync_state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-platform Astra workspace sync")
    parser.add_argument(
        "--target",
        default=r"X:\CODEX_5.5_redactor\Codex_6\056_Asttra",
    )
    parser.add_argument("--repo", default=REPO)
    parser.add_argument("--branch", default=BRANCH)
    args = parser.parse_args()

    state = sync_workspace(Path(args.target), repo=args.repo, branch=args.branch)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
