from pathlib import Path

from journal_factory.skills_loader import EXPECTED_MASTER_VERSION, REQUIRED_MODULES, load_skill_registry, sha256_file


def _write_skill(root: Path, *, version: str = EXPECTED_MASTER_VERSION, malformed: bool = False) -> None:
    skill_dir = root / "skills" / "journal"
    skill_dir.mkdir(parents=True)
    if malformed:
        skill_dir.joinpath("SKILL.md").write_text("---\nname journal\n---\nbody\n", encoding="utf-8")
        return
    skill_dir.joinpath("SKILL.md").write_text(
        f"---\nname: journal\nmetadata:\n  version: \"{version}\"\n---\n# Journal\n",
        encoding="utf-8",
    )


def _write_module(root: Path, name: str, folder: str | None = None, body: str = "# Procedure\n") -> None:
    module_dir = root / "skills" / (folder or name)
    module_dir.mkdir(parents=True)
    module_dir.joinpath("MODULE.md").write_text(
        f"---\nname: {name}\nmetadata:\n  version: \"1.0.0\"\n---\n{body}",
        encoding="utf-8",
    )


def _write_required_modules(root: Path) -> None:
    for name in REQUIRED_MODULES:
        _write_module(root, name)


def test_valid_v35_skill_registry_from_repository() -> None:
    registry = load_skill_registry(Path("agent_skills") / "NAUKAINFO_Agent_Skills_v3_5")

    assert registry.registry_status == "PASS"
    assert registry.master_skill == "journal"
    assert registry.version == EXPECTED_MASTER_VERSION
    assert registry.module_count >= len(REQUIRED_MODULES)
    assert registry.missing_required_modules == []
    assert all(module.internal_only for module in registry.modules)


def test_missing_master_skill(tmp_path: Path) -> None:
    _write_required_modules(tmp_path)

    registry = load_skill_registry(tmp_path)

    assert registry.registry_status == "BLOCKED"
    assert "master_skill_missing" in registry.blockers


def test_wrong_master_version(tmp_path: Path) -> None:
    _write_skill(tmp_path, version="3.4.0")
    _write_required_modules(tmp_path)

    registry = load_skill_registry(tmp_path)

    assert registry.registry_status == "BLOCKED"
    assert "master_skill_version_invalid" in registry.blockers


def test_duplicate_module(tmp_path: Path) -> None:
    _write_skill(tmp_path)
    _write_required_modules(tmp_path)
    _write_module(tmp_path, REQUIRED_MODULES[0], folder="duplicate-folder")

    registry = load_skill_registry(tmp_path)

    assert registry.registry_status == "BLOCKED"
    assert f"duplicate_module:{REQUIRED_MODULES[0]}" in registry.blockers


def test_malformed_yaml_frontmatter(tmp_path: Path) -> None:
    _write_skill(tmp_path, malformed=True)
    _write_required_modules(tmp_path)

    registry = load_skill_registry(tmp_path)

    assert registry.registry_status == "BLOCKED"
    assert any(item.startswith("master_skill_unparseable") for item in registry.blockers)


def test_missing_required_module(tmp_path: Path) -> None:
    _write_skill(tmp_path)
    for name in REQUIRED_MODULES[1:]:
        _write_module(tmp_path, name)

    registry = load_skill_registry(tmp_path)

    assert registry.registry_status == "BLOCKED"
    assert registry.missing_required_modules == [REQUIRED_MODULES[0]]


def test_stable_sha256(tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    path.write_text("same content", encoding="utf-8")

    assert sha256_file(path) == sha256_file(path)
