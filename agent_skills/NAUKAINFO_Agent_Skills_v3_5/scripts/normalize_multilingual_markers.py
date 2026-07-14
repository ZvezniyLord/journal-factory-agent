#!/usr/bin/env python3
"""Shared multilingual marker recognition for NAUKAINFO journal normalization.

This module classifies reference headings, figure captions, and table labels. It
is intentionally conservative: classification does not rewrite article prose.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

REFERENCE_MARKERS = {
    "uk": [
        r"список\s+використаних\s+джерел", r"список\s+джерел",
        r"список\s+літератури", r"використан[аі]\s+літератур[аи]", r"література",
    ],
    "en": [r"references?", r"reference\s+list", r"bibliography", r"works\s+cited"],
    "de": [r"literaturverzeichnis", r"quellenverzeichnis", r"literatur", r"quellen"],
    "pl": [r"bibliografia", r"literatura", r"wykaz\s+źródeł"],
    "cs": [r"seznam\s+použité\s+literatury", r"literatura", r"zdroje"],
    "sk": [r"zoznam\s+použitej\s+literatúry", r"literatúra", r"zdroje"],
    "fr": [r"références", r"bibliographie", r"sources"],
}

FIGURE_PREFIXES = {
    "uk": ("рис.", "рисунок", "мал.", "малюнок"),
    "en": ("fig.", "figure"),
    "de": ("abb.", "abbildung"),
    "pl": ("rys.", "rycina"),
    "cs": ("obr.", "obrázek"),
    "sk": ("obr.", "obrázok"),
    "fr": ("fig.", "figure"),
}

TABLE_PREFIXES = {
    "uk": ("таблиця",),
    "en": ("table",),
    "de": ("tabelle",),
    "pl": ("tabela",),
    "cs": ("tabulka",),
    "sk": ("tabuľka",),
    "fr": ("tableau",),
}

CANONICAL_REFERENCE_HEADING = {
    "uk": "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:",
    "en": "REFERENCES",
    "de": None,  # preserve standard German distinction: Literatur-/Quellenverzeichnis
    "pl": "BIBLIOGRAFIA",
    "cs": "LITERATURA",
    "sk": "LITERATÚRA",
    "fr": "RÉFÉRENCES",
}


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace("\u00a0", " ")).strip()


def strip_leading_section_number(text: str) -> str:
    return re.sub(r"^\s*(?:\d{1,3}[\.)]|[IVXLCDM]+[\.)])\s*", "", norm(text), flags=re.I)


def classify_reference_heading(text: str) -> tuple[str | None, str | None]:
    candidate = strip_leading_section_number(text).rstrip(".:; ").casefold()
    for lang, patterns in REFERENCE_MARKERS.items():
        for pattern in patterns:
            if re.fullmatch(pattern, candidate, flags=re.I):
                canonical = CANONICAL_REFERENCE_HEADING[lang]
                if lang == "de":
                    canonical = "LITERATURVERZEICHNIS:" if "literatur" in candidate else "QUELLENVERZEICHNIS:"
                return lang, canonical
    return None, None


def is_figure_caption(text: str) -> bool:
    t = norm(text).casefold()
    if re.match(r"^agd\s*\d+\b", t):
        return True
    return any(t.startswith(prefix) for prefixes in FIGURE_PREFIXES.values() for prefix in prefixes)


def is_table_label(text: str) -> bool:
    t = norm(text).casefold().rstrip(".: ")
    return any(t == p or re.match(rf"^{re.escape(p)}\s*\d+[a-zа-яіїєґ-]*\b", t, re.I)
               for prefixes in TABLE_PREFIXES.values() for p in prefixes)


def split_table_label_title(text: str) -> tuple[str, str] | None:
    """Split `Таблиця 1 – Назва`/`Table 2: Title`; preserve title verbatim."""
    t = norm(text)
    prefix = "|".join(re.escape(p) for ps in TABLE_PREFIXES.values() for p in ps)
    m = re.match(rf"^((?:{prefix})\s*\d+[A-Za-zА-Яа-яІіЇїЄєҐґ-]*)\s*(?:[-–—:])\s*(.+)$", t, re.I)
    return (m.group(1), m.group(2)) if m else None

if __name__ == "__main__":
    import argparse, json
    ap=argparse.ArgumentParser(); ap.add_argument("text"); args=ap.parse_args()
    print(json.dumps({
        "reference": classify_reference_heading(args.text),
        "figure_caption": is_figure_caption(args.text),
        "table_label": is_table_label(args.text),
        "table_split": split_table_label_title(args.text),
    }, ensure_ascii=False, indent=2))
