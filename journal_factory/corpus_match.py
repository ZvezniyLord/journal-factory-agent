from __future__ import annotations

import difflib
import re
from dataclasses import asdict, dataclass

from .corpus_pdf import GoldenArticle
from .corpus_extract import ExtractedDocument
from .corpus_utils import normalize_space, tokenize

ANNOTATION_RE = re.compile(r"^(?:Abstract|Анотац|Аннотац|Keywords|Ключові слова)", re.IGNORECASE)
UDC_RE = re.compile(r"^(?:UDC|УДК)\b", re.IGNORECASE)


@dataclass(frozen=True)
class RawProfile:
    path: str
    sha256: str
    title: str
    authors: tuple[str, ...]
    udc: str | None
    body_preview: str
    word_count: int


@dataclass(frozen=True)
class Alignment:
    article_id: str
    golden_title: str
    golden_authors: tuple[str, ...]
    selected_raw_path: str | None
    selected_raw_sha256: str | None
    score: float
    title_score: float
    author_score: float
    body_score: float
    candidate_gap: float
    confidence: str
    status: str
    alternatives: tuple[dict, ...]

    def to_record(self) -> dict:
        return asdict(self)


def _upper_ratio(value: str) -> float:
    letters = [c for c in value if c.isalpha()]
    return sum(c.isupper() for c in letters) / len(letters) if letters else 0.0


def _name_like(line: str) -> bool:
    low = line.casefold()
    if any(x in low for x in ("університет", "інститут", "кафедр", "phd", "доктор", "доцент", "orcid", "@")):
        return False
    tokens = [x.strip(",.;:") for x in line.split() if any(c.isalpha() for c in x)]
    return 2 <= len(tokens) <= 12 and sum(x[:1].isupper() for x in tokens) / len(tokens) >= 0.7


def profile_raw(document: ExtractedDocument) -> RawProfile:
    lines = [normalize_space(x) for x in document.text.splitlines() if normalize_space(x)]
    udc = next((UDC_RE.sub("", x).strip(" :.") for x in lines[:30] if UDC_RE.match(x)), None)
    explicit_marker = next((i for i, line in enumerate(lines[:80]) if ANNOTATION_RE.match(line)), None)
    header_limit = explicit_marker if explicit_marker is not None else min(len(lines), 45)
    header = lines[:header_limit]
    title_start = next((
        i for i, line in enumerate(header)
        if not UDC_RE.match(line)
        and _upper_ratio(line) >= 0.72
        and len(line) >= 8
    ), None)
    if title_start is None:
        title = ""
        title_end = 0
    else:
        title_end = title_start
        while title_end < len(header):
            line = header[title_end]
            if _upper_ratio(line) < 0.52 and title_end > title_start:
                break
            title_end += 1
        title = normalize_space(" ".join(header[title_start:title_end]))
    authors = tuple(x.rstrip(",.;") for x in header[: title_start or 0] if _name_like(x))
    body_start = explicit_marker if explicit_marker is not None else title_end
    body_preview = normalize_space(" ".join(lines[body_start : body_start + 25]))
    return RawProfile(document.path, document.sha256, title, authors, udc, body_preview, document.word_count)


def _ratio(left: str, right: str) -> float:
    a, b = normalize_space(left).casefold(), normalize_space(right).casefold()
    if not a or not b:
        return 0.0
    try:
        from rapidfuzz.fuzz import ratio
        return ratio(a, b) / 100.0
    except ImportError:
        return difflib.SequenceMatcher(None, a, b, autojunk=True).quick_ratio()


def _token_overlap(left: str, right: str) -> float:
    a, b = set(tokenize(left)), set(tokenize(right))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _author_score(golden: tuple[str, ...], raw: tuple[str, ...]) -> float:
    if not golden or not raw:
        return 0.0
    return _token_overlap(" ".join(golden), " ".join(raw))


def score_pair(article: GoldenArticle, raw: RawProfile) -> dict:
    title = max(_ratio(article.title, raw.title), _token_overlap(article.title, raw.title))
    authors = _author_score(article.authors, raw.authors)
    body = _token_overlap(article.body_preview, raw.body_preview)
    total = 0.55 * title + 0.20 * authors + 0.25 * body
    return {
        "raw_path": raw.path,
        "raw_sha256": raw.sha256,
        "score": round(total, 6),
        "title_score": round(title, 6),
        "author_score": round(authors, 6),
        "body_score": round(body, 6),
    }


def align_articles(articles: list[GoldenArticle], raw_profiles: list[RawProfile]) -> list[Alignment]:
    used: set[str] = set()
    results: list[Alignment] = []
    for article in articles:
        ranked = sorted((score_pair(article, raw) for raw in raw_profiles), key=lambda x: x["score"], reverse=True)
        available = [row for row in ranked if row["raw_sha256"] not in used]
        best = available[0] if available else None
        second = available[1] if len(available) > 1 else None
        if not best:
            results.append(Alignment(article.article_id, article.title, article.authors, None, None, 0, 0, 0, 0, 0, "NONE", "UNMATCHED", ()))
            continue
        gap = best["score"] - (second["score"] if second else 0.0)
        if best["score"] >= 0.84 and gap >= 0.06:
            confidence, status = "HIGH", "MATCHED_HIGH"
            used.add(best["raw_sha256"])
        elif best["score"] >= 0.68 and gap >= 0.035:
            confidence, status = "MEDIUM", "REVIEW"
        elif best["score"] >= 0.52:
            confidence, status = "LOW", "REVIEW"
        else:
            confidence, status = "NONE", "UNMATCHED"
        results.append(Alignment(
            article_id=article.article_id,
            golden_title=article.title,
            golden_authors=article.authors,
            selected_raw_path=best["raw_path"] if status != "UNMATCHED" else None,
            selected_raw_sha256=best["raw_sha256"] if status != "UNMATCHED" else None,
            score=best["score"],
            title_score=best["title_score"],
            author_score=best["author_score"],
            body_score=best["body_score"],
            candidate_gap=round(gap, 6),
            confidence=confidence,
            status=status,
            alternatives=tuple(ranked[:3]),
        ))
    return results
