from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path


class IntakeBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class InventoryItem:
    relative_path: str
    suffix: str
    size: int
    sha256: str
    kind: str


@dataclass(frozen=True)
class IntakeResult:
    archive_path: str
    conference_number: str
    extracted_root: str
    registry_candidates: list[str]
    article_candidates: list[str]
    questionnaire_candidates: list[str]
    template_candidates: list[str]
    inventory: list[InventoryItem]
    warnings: list[str]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_conference_number(name: str) -> str:
    matches = re.findall(r"(?<!\d)(\d{3,})(?!\d)", name)
    if not matches:
        raise IntakeBlocked("UNRESOLVED_CONFERENCE_NUMBER")
    first = matches[0]
    if any(m != first for m in matches[1:]):
        raise IntakeBlocked(f"AMBIGUOUS_CONFERENCE_NUMBER:{matches}")
    return first


def _safe_target(root: Path, member_name: str) -> Path:
    member = Path(member_name.replace("\\", "/"))
    if member.is_absolute() or ".." in member.parts:
        raise IntakeBlocked(f"UNSAFE_ARCHIVE_MEMBER:{member_name}")
    target = (root / member).resolve()
    if root.resolve() not in target.parents and target != root.resolve():
        raise IntakeBlocked(f"ARCHIVE_ESCAPE:{member_name}")
    return target


def _extract_zip(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            target = _safe_target(destination, info.filename)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def _extract_with_7z(archive: Path, destination: Path, executable: str = "7z") -> None:
    proc = subprocess.run(
        [executable, "x", "-y", f"-o{destination}", str(archive)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise IntakeBlocked("RAR_EXTRACTION_FAILED:" + proc.stdout[-4000:].replace("\n", " "))


def _classify(rel: str, suffix: str) -> str:
    name = Path(rel).name.casefold()
    if suffix in {".xlsx", ".xlsm"}:
        return "REGISTRY_OR_SPREADSHEET"
    if suffix in {".dotx", ".dotm"}:
        return "TEMPLATE"
    if suffix in {".doc", ".docx"}:
        if any(x in name for x in ("анк", "questionnaire", "application", "заяв", "форма")):
            return "QUESTIONNAIRE"
        return "ARTICLE_OR_DOC"
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".svg"}:
        return "IMAGE"
    return "OTHER"


def inventory_tree(root: Path) -> list[InventoryItem]:
    items: list[InventoryItem] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.casefold()
        items.append(
            InventoryItem(
                relative_path=rel,
                suffix=suffix,
                size=path.stat().st_size,
                sha256=_sha256(path),
                kind=_classify(rel, suffix),
            )
        )
    return items


def _pick_registry_candidates(items: list[InventoryItem]) -> list[str]:
    xlsx = [i for i in items if i.suffix in {".xlsx", ".xlsm"}]
    ranked = sorted(
        xlsx,
        key=lambda i: (
            0 if any(k in i.relative_path.casefold() for k in ("учас", "participant", "реєстр", "registry")) else 1,
            i.relative_path.casefold(),
        ),
    )
    return [i.relative_path for i in ranked]


def extract_and_inventory(
    archive_path: str | Path,
    work_root: str | Path,
    *,
    seven_zip_executable: str = "7z",
) -> IntakeResult:
    archive = Path(archive_path).resolve()
    if not archive.exists():
        raise IntakeBlocked(f"ARCHIVE_NOT_FOUND:{archive}")

    conference_number = detect_conference_number(archive.name)
    destination = Path(work_root).resolve() / "extracted"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    suffix = archive.suffix.casefold()
    if suffix == ".zip":
        _extract_zip(archive, destination)
    elif suffix in {".rar", ".7z"}:
        _extract_with_7z(archive, destination, seven_zip_executable)
    else:
        raise IntakeBlocked(f"UNSUPPORTED_ARCHIVE_TYPE:{suffix}")

    items = inventory_tree(destination)
    registry = _pick_registry_candidates(items)
    articles = [i.relative_path for i in items if i.kind == "ARTICLE_OR_DOC"]
    questionnaires = [i.relative_path for i in items if i.kind == "QUESTIONNAIRE"]
    templates = [i.relative_path for i in items if i.kind == "TEMPLATE"]

    warnings: list[str] = []
    if not registry:
        warnings.append("NO_REGISTRY_CANDIDATE")
    elif len(registry) > 1:
        warnings.append("MULTIPLE_REGISTRY_CANDIDATES")
    if not articles:
        warnings.append("NO_ARTICLE_CANDIDATES")

    return IntakeResult(
        archive_path=str(archive),
        conference_number=conference_number,
        extracted_root=str(destination),
        registry_candidates=registry,
        article_candidates=articles,
        questionnaire_candidates=questionnaires,
        template_candidates=templates,
        inventory=items,
        warnings=warnings,
    )


def write_intake_result(path: str | Path, result: IntakeResult) -> None:
    Path(path).write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
