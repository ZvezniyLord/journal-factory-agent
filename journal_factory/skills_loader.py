from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import os
from typing import Any


EXPECTED_MASTER_NAME = "journal"
EXPECTED_MASTER_VERSION = "3.5.0"
DEFAULT_SKILL_ROOT = Path("agent_skills") / "NAUKAINFO_Agent_Skills_v3_5"
REQUIRED_MODULES = [
    "naukainfo-preflight",
    "naukainfo-manifest-evidence-matching",
    "naukainfo-author-body-fidelity",
    "naukainfo-front-matter-order-and-title-dedupe",
    "naukainfo-udc-review",
    "naukainfo-canonical-style-application",
    "naukainfo-reference-block-fidelity",
    "naukainfo-reference-entry-reconstruction",
    "naukainfo-table-figure-caption-contract",
    "naukainfo-shape-object-fidelity",
    "naukainfo-multi-article-assembly",
    "naukainfo-toc-table-builder",
    "naukainfo-free-listener-toc-section",
    "naukainfo-visual-regression",
    "naukainfo-quality-gate",
]


@dataclass(frozen=True)
class SkillModule:
    name: str
    source_path: str
    sha256: str
    version: str | None
    internal_only: bool = True


@dataclass(frozen=True)
class SkillRegistry:
    master_skill: str | None
    version: str | None
    source_path: str | None
    sha256: str | None
    modules: list[SkillModule]
    module_count: int
    required_modules: list[str]
    missing_required_modules: list[str]
    loaded_at: str
    registry_status: str
    blockers: list[str]
    warnings: list[str]

    def to_manifest(self) -> dict[str, Any]:
        data = asdict(self)
        data["modules"] = [asdict(module) for module in self.modules]
        return data


class SkillRegistryError(ValueError):
    pass


def default_skill_root() -> Path:
    value = os.environ.get("AGENT_SKILLS_ROOT")
    if value:
        root = Path(value)
        if (root / "skills" / "journal" / "SKILL.md").exists():
            return root
        nested = root / "NAUKAINFO_Agent_Skills_v3_5"
        if (nested / "skills" / "journal" / "SKILL.md").exists():
            return nested
    return DEFAULT_SKILL_ROOT


def load_skill_registry(skill_root: Path | None = None) -> SkillRegistry:
    root = skill_root or default_skill_root()
    root = root.resolve()
    loaded_at = datetime.now(timezone.utc).isoformat()
    blockers: list[str] = []
    warnings: list[str] = []
    modules: list[SkillModule] = []
    master_name: str | None = None
    master_version: str | None = None
    master_sha: str | None = None
    master_path = root / "skills" / "journal" / "SKILL.md"

    if not master_path.exists():
        blockers.append("master_skill_missing")
    else:
        try:
            master_sha = sha256_file(master_path)
            frontmatter, body = read_frontmatter(master_path)
            master_name = str(frontmatter.get("name") or "")
            metadata = frontmatter.get("metadata") if isinstance(frontmatter.get("metadata"), dict) else {}
            master_version = str(metadata.get("version") or frontmatter.get("version") or "")
            if master_name != EXPECTED_MASTER_NAME:
                blockers.append("master_skill_name_invalid")
            if master_version != EXPECTED_MASTER_VERSION:
                blockers.append("master_skill_version_invalid")
            if not body.strip():
                blockers.append("master_skill_empty")
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"master_skill_unparseable:{type(exc).__name__}")

    seen: set[str] = set()
    module_errors: list[str] = []
    for module_path in sorted((root / "skills").glob("*/MODULE.md")):
        try:
            module_sha = sha256_file(module_path)
            frontmatter, body = read_frontmatter(module_path)
            name = str(frontmatter.get("name") or "")
            if not name:
                module_errors.append(f"module_name_missing:{module_path}")
                continue
            if name in seen:
                module_errors.append(f"duplicate_module:{name}")
                continue
            if not body.strip():
                module_errors.append(f"module_empty:{name}")
                continue
            metadata = frontmatter.get("metadata") if isinstance(frontmatter.get("metadata"), dict) else {}
            modules.append(
                SkillModule(
                    name=name,
                    source_path=str(module_path),
                    sha256=module_sha,
                    version=str(metadata.get("version")) if metadata.get("version") is not None else None,
                )
            )
            seen.add(name)
        except Exception as exc:  # noqa: BLE001
            module_errors.append(f"module_unparseable:{module_path}:{type(exc).__name__}")

    blockers.extend(module_errors)
    found = {module.name for module in modules}
    missing_required = [name for name in REQUIRED_MODULES if name not in found]
    if missing_required:
        blockers.extend(f"required_module_missing:{name}" for name in missing_required)

    status = "PASS" if not blockers else "BLOCKED"
    return SkillRegistry(
        master_skill=master_name,
        version=master_version,
        source_path=str(master_path) if master_path.exists() else None,
        sha256=master_sha,
        modules=modules,
        module_count=len(modules),
        required_modules=list(REQUIRED_MODULES),
        missing_required_modules=missing_required,
        loaded_at=loaded_at,
        registry_status=status,
        blockers=blockers,
        warnings=warnings,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    if not text.startswith("---\n"):
        raise SkillRegistryError("missing YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise SkillRegistryError("unterminated YAML frontmatter")
    raw = text[4:end].strip("\n")
    body = text[end + 4 :]
    return parse_simple_yaml(raw), body


def parse_simple_yaml(raw: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    current_map: dict[str, str] | None = None
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  "):
            if current_map is None or current_key is None:
                raise SkillRegistryError(f"unexpected indentation: {line}")
            child = line.strip()
            if ":" not in child:
                raise SkillRegistryError(f"invalid YAML line: {line}")
            key, value = child.split(":", 1)
            current_map[key.strip()] = _clean_scalar(value)
            continue
        current_map = None
        current_key = None
        if ":" not in line:
            raise SkillRegistryError(f"invalid YAML line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        if not value.strip():
            nested: dict[str, str] = {}
            result[key] = nested
            current_key = key
            current_map = nested
        else:
            result[key] = _clean_scalar(value)
    return result


def _clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
