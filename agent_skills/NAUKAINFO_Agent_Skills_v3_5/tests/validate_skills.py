from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise AssertionError("SKILL.md must start with YAML frontmatter")
    _, front, _body = text.split("---", 2)
    result = {}
    for line in front.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def main() -> None:
    skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert skills, "no skills found"
    for path in skills:
        text = path.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        name = meta.get("name", "")
        description = meta.get("description", "")
        assert name == path.parent.name, (path, name)
        assert NAME_RE.fullmatch(name), name
        assert 1 <= len(name) <= 64, name
        assert 1 <= len(description) <= 1024, path
        assert len(text.splitlines()) < 500, f"SKILL.md too long: {path}"
    print(f"Validated {len(skills)} skills")


if __name__ == "__main__":
    main()
