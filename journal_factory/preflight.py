from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import os

from .config import AppConfig


@dataclass
class CheckResult:
    name: str
    path: str
    ok: bool
    required: bool
    message: str


MANDATORY_SOURCE_PACK_FILES = [
    "README_FOR_CODEX.md",
    "new_version_spec/CURRENT_RULES_2026.md",
    "new_version_spec/CURRENT_RULES_2026.json",
    "new_version_spec/DATABASE_JSON_CONCEPT.md",
    "new_version_spec/PROMPT_FOR_NEW_CODEX.md",
]


def _exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def _find_journal_skill() -> list[Path]:
    env_root = os.environ.get("AGENT_SKILLS_ROOT")
    roots = [
        Path.home() / ".codex",
        Path.cwd() / ".codex",
        Path.cwd() / "agent_skills",
    ]
    if env_root:
        roots.append(Path(env_root))
    candidates: list[Path] = []
    for root in roots:
        candidates.extend(root.glob("skills/**/SKILL.md"))
        candidates.extend(root.glob("plugins/**/SKILL.md"))
        candidates.extend(root.glob("**/SKILL.md"))

    matches: list[Path] = []
    for path in dict.fromkeys(candidates):
        content = path.read_text(encoding="utf-8", errors="ignore").lower()[:4000]
        if ("журнал" in content or "journal" in content) and ("3.2" in content or "journal factory" in content):
            matches.append(path)
    return matches


def _find_control_files(source_pack: Path) -> list[Path]:
    if not _exists(source_pack):
        return []
    matches: list[Path] = []
    for path in source_pack.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        rel = path.relative_to(source_pack).as_posix().lower()
        if (
            "quality_gate" in name
            or "final_quality_gate" in name
            or name.startswith("test_")
            or "/tests/" in rel
            or "audit" in name
            or "control" in name
            or "контроль" in name
        ):
            matches.append(path)
    return matches


def run_preflight(config: AppConfig) -> dict:
    checks: list[CheckResult] = []

    checks.append(CheckResult("archive", str(config.archive), _exists(config.archive), True, "Author submissions ZIP or folder"))
    checks.append(CheckResult("etalon", str(config.etalon), _exists(config.etalon), True, "ETALON-JOURNAL.docx"))
    checks.append(CheckResult("template", str(config.template), _exists(config.template), True, "Jurnal.dotx"))
    checks.append(CheckResult("source_pack", str(config.source_pack), _exists(config.source_pack), True, "Clean requirements pack"))

    for rel in MANDATORY_SOURCE_PACK_FILES:
        checks.append(CheckResult(f"source_pack:{rel}", str(config.source_pack / rel), _exists(config.source_pack / rel), True, rel))

    journal_skill = _find_journal_skill()
    checks.append(
        CheckResult(
            "active_skill_journal_v3_2",
            "; ".join(map(str, journal_skill)),
            bool(journal_skill),
            False,
            "Codex journal skill is optional inside Docker runtime",
        )
    )

    control_files = _find_control_files(config.source_pack)
    checks.append(
        CheckResult(
            "acceptance_qa_control_files",
            "; ".join(map(str, control_files[:20])),
            bool(control_files),
            True,
            "Acceptance tests, QA schemas, or quality gate controls",
        )
    )

    blockers = [check for check in checks if check.required and not check.ok]
    status = "BUILD BLOCKED" if blockers else "READY"
    return {
        "status": status,
        "checks": [asdict(check) for check in checks],
        "blockers": [asdict(check) for check in blockers],
    }


def write_preflight(config: AppConfig, result: dict) -> Path:
    path = config.reports_dir / "preflight.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
