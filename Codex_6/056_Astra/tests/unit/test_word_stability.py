from lxml import etree
import pytest

from astra_journal.word_stability import harden_styles_xml, inspect_styles_xml

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _styles() -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<w:styles xmlns:w="{W}">
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="SECTION">
    <w:name w:val="SECTION"/>
    <w:autoRedefine/>
    <w:rPr>
      <w:rFonts w:asciiTheme="minorHAnsi" w:hAnsiTheme="minorHAnsi"/>
    </w:rPr>
  </w:style>
</w:styles>""".encode()


def test_inspector_finds_auto_redefine_and_theme_dependency() -> None:
    report = inspect_styles_xml(_styles())
    assert report["auto_redefine"][0]["style_id"] == "SECTION"
    assert report["theme_font_dependencies"][0]["style_id"] == "SECTION"


def test_hardening_makes_target_style_explicit() -> None:
    fixed = harden_styles_xml(
        _styles(),
        style_ids={"SECTION"},
        font_name="Times New Roman",
        size_pt=11,
        alignment="center",
        after_twips=0,
    )
    report = inspect_styles_xml(fixed)
    assert report["auto_redefine"] == []
    assert report["theme_font_dependencies"] == []

    root = etree.fromstring(fixed)
    ns = {"w": W}
    style = root.xpath('//w:style[@w:styleId="SECTION"]', namespaces=ns)[0]
    fonts = style.find("w:rPr/w:rFonts", ns)
    assert fonts.get(f"{{{W}}}ascii") == "Times New Roman"
    assert fonts.get(f"{{{W}}}hAnsi") == "Times New Roman"


def test_hardening_refuses_normal() -> None:
    with pytest.raises(ValueError):
        harden_styles_xml(_styles(), style_ids={"Normal"})
