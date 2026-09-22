from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class ParagraphRole(StrEnum):
    SECTION_TITLE = "SECTION_TITLE"
    DOI = "DOI"
    UDC = "UDC"
    AUTHOR = "AUTHOR"
    SUPERVISOR = "SUPERVISOR"
    AFFILIATION = "AFFILIATION"
    POSITION_DEGREE = "POSITION_DEGREE"
    ORCID = "ORCID"
    TITLE = "TITLE"
    ABSTRACT = "ABSTRACT"
    KEYWORDS = "KEYWORDS"
    BODY = "BODY"
    SUBHEADING = "SUBHEADING"
    TABLE_CAPTION = "TABLE_CAPTION"
    TABLE_SOURCE = "TABLE_SOURCE"
    FIGURE_CAPTION = "FIGURE_CAPTION"
    FIGURE_SOURCE = "FIGURE_SOURCE"
    REF_TITLE = "REF_TITLE"
    REFERENCE = "REFERENCE"
    REFERENCE_CONTINUATION = "REFERENCE_CONTINUATION"
    SPECIAL_THANKS = "SPECIAL_THANKS"
    OTHER = "OTHER"


@dataclass(frozen=True)
class RoleGuess:
    role: ParagraphRole
    confidence: float
    evidence: tuple[str, ...]


_RULES = [
    (ParagraphRole.UDC, re.compile(r"^\s*(УДК|UDC)\b", re.I), .995, "udc-prefix"),
    (ParagraphRole.DOI, re.compile(r"^\s*(DOI\s*:?\s*)?10\.\d{4,9}/\S+", re.I), .995, "doi"),
    (ParagraphRole.ORCID, re.compile(r"\bORCID\b", re.I), .995, "orcid"),
    (ParagraphRole.SUPERVISOR, re.compile(r"^\s*(науков(ий|а)\s+керівник|scientific\s+supervisor|research\s+supervisor|supervisor|научный\s+руководитель)\b", re.I), .99, "supervisor-label"),
    (ParagraphRole.ABSTRACT, re.compile(r"^\s*(анотація|abstract|аннотация)\b", re.I), .99, "abstract-label"),
    (ParagraphRole.KEYWORDS, re.compile(r"^\s*(ключові\s+слова|keywords|ключевые\s+слова)\b", re.I), .99, "keywords-label"),
    (ParagraphRole.REF_TITLE, re.compile(r"^\s*(references?|referens|referenses|література|список\s+використаних\s+(джерел|літератури)|список\s+літератури|бібліографія|list\s+of\s+references|bibliography)\s*:?\s*$", re.I), .99, "reference-heading"),
    (ParagraphRole.TABLE_CAPTION, re.compile(r"^\s*(таблиця|table|таблица)\s*\d*([.:–—-]|\s)", re.I), .985, "table-caption-prefix"),
    (ParagraphRole.FIGURE_CAPTION, re.compile(r"^\s*(рис\.?|рисунок|figure|fig\.?|мал\.?|малюнок)\s*\d*([.:–—-]|\s)", re.I), .985, "figure-caption-prefix"),
    (ParagraphRole.TABLE_SOURCE, re.compile(r"^\s*(джерело|source|источник)\s*:", re.I), .97, "source-label"),
    (ParagraphRole.FIGURE_SOURCE, re.compile(r"^\s*(джерело|source|источник)\s*:", re.I), .97, "source-label"),
]


def deterministic_role(text: str) -> RoleGuess | None:
    normalized = " ".join(text.split())
    if not normalized:
        return None
    for role, pattern, confidence, evidence in _RULES:
        if pattern.search(normalized):
            return RoleGuess(role, confidence, (evidence,))
    return None
