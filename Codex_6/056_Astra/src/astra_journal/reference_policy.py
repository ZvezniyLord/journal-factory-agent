from __future__ import annotations

import re
from dataclasses import dataclass

UK_CANONICAL = "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ"
EN_CANONICAL = "REFERENCES"


def _norm(text: str) -> str:
    value = text.strip().casefold()
    value = value.replace("’", "'").replace("\u0060", "'")
    value = re.sub(r"[\s\u00a0]+", " ", value)
    value = re.sub(r"[:.;,\-–—]+$", "", value).strip()
    return value


_UK_VARIANTS = {_norm(x) for x in [
    "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ",
    "СПИСОК ВИКОРИСТАНОЇ ЛІТЕРАТУРИ",
    "СПИСОК ВИКОРИСТАНИХ ЛІТЕРАТУРНИХ ДЖЕРЕЛ",
    "ВИКОРИСТАНІ ДЖЕРЕЛА",
    "ЛІТЕРАТУРА",
    "СПИСОК ЛІТЕРАТУРИ",
    "БІБЛІОГРАФІЯ",
    "ДЖЕРЕЛА",
]}

_EN_VARIANTS = {_norm(x) for x in [
    "REFERENCES",
    "REFERENCE",
    "REFERENS",
    "REFERENSES",
    "REFERENCES LIST",
    "BIBLIOGRAPHY",
    "LIST OF REFERENCES",
    "SOURCES",
]}


@dataclass(frozen=True)
class ReferenceHeadingNormalization:
    matched: bool
    source: str
    canonical: str | None
    language: str | None
    reason: str | None


def normalize_reference_heading(
    text: str,
    *,
    article_language: str | None = None,
) -> ReferenceHeadingNormalization:
    normalized = _norm(text)

    if normalized in _UK_VARIANTS:
        return ReferenceHeadingNormalization(
            True, text, UK_CANONICAL, "uk", "recognized-uk-reference-heading"
        )

    if normalized in _EN_VARIANTS:
        return ReferenceHeadingNormalization(
            True, text, EN_CANONICAL, "en", "recognized-en-reference-heading"
        )

    compact = re.sub(r"[^a-z]", "", normalized)
    if compact.startswith("refer") and len(compact) <= 14:
        canonical = UK_CANONICAL if article_language == "uk" else EN_CANONICAL
        language = "uk" if article_language == "uk" else "en"
        return ReferenceHeadingNormalization(
            True, text, canonical, language, "reference-heading-typo-normalization"
        )

    return ReferenceHeadingNormalization(False, text, None, None, None)
