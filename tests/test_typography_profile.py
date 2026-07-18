from __future__ import annotations

from pathlib import Path
import json
import zipfile

from docx import Document
from lxml import etree

from journal_factory.typography_profile import apply_typography_profile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
W_VAL = f"{{{W_NS}}}val"


def test_legacy_profile_sets_default_body_to_14pt(tmp_path: Path) -> None:
    result = _apply(tmp_path, "legacy_14pt")
    assert result["body_font_size_pt"] == 14
    assert _default_sizes(Path(result["output"])) == ("28", "28")


def test_new_standard_sets_default_body_to_11pt(tmp_path: Path) -> None:
    result = _apply(tmp_path, "standard_11pt")
    assert result["body_font_size_pt"] == 11
    assert _default_sizes(Path(result["output"])) == ("22", "22")


def _apply(tmp_path: Path, profile: str) -> dict:
    source = tmp_path / "source.docx"
    output = tmp_path / f"{profile}.docx"
    profiles = tmp_path / "profiles.json"
    Document().save(source)
    profiles.write_text(
        json.dumps(
            {
                "profiles": {
                    "legacy_14pt": {"body_font_size_pt": 14},
                    "standard_11pt": {"body_font_size_pt": 11}
                }
            }
        ),
        encoding="utf-8",
    )
    return apply_typography_profile(source, output, profiles, profile)


def _default_sizes(path: Path) -> tuple[str | None, str | None]:
    with zipfile.ZipFile(path) as package:
        root = etree.fromstring(package.read("word/styles.xml"))
    style = root.xpath(
        "./w:style[@w:type='paragraph' and @w:default='1']",
        namespaces=NS,
    )[0]
    size = style.find("w:rPr/w:sz", namespaces=NS)
    size_cs = style.find("w:rPr/w:szCs", namespaces=NS)
    return (
        size.get(W_VAL) if size is not None else None,
        size_cs.get(W_VAL) if size_cs is not None else None,
    )
