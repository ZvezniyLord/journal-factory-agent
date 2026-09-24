from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


def normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    text = text.casefold().replace("’", "'")
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class MatchCandidate:
    source_path: str
    score: float
    evidence: tuple[str, ...]


def title_similarity(a: str, b: str) -> float:
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    return SequenceMatcher(None, na, nb).ratio()


def rank_article_candidates(
    registry_title: str,
    source_records: list[dict[str, Any]],
    *,
    limit: int = 5,
) -> list[MatchCandidate]:
    ranked: list[MatchCandidate] = []
    for record in source_records:
        source_path = str(record.get("path", ""))
        title_candidates = list(record.get("title_candidates", []))
        if not title_candidates:
            title_candidates = [
                p.get("text", "")
                for p in record.get("excerpt", [])[:20]
                if p.get("text")
            ]
        best = 0.0
        best_text = ""
        for candidate in title_candidates:
            score = title_similarity(registry_title, candidate)
            if score > best:
                best = score
                best_text = candidate
        if best:
            ranked.append(
                MatchCandidate(
                    source_path=source_path,
                    score=best,
                    evidence=(f"title:{best_text}",),
                )
            )
    ranked.sort(key=lambda x: (-x.score, x.source_path.casefold()))
    return ranked[:limit]


def deterministic_match(
    registry_title: str,
    source_records: list[dict[str, Any]],
    *,
    auto_accept: float = 0.96,
    ambiguity_margin: float = 0.04,
) -> dict[str, Any]:
    ranked = rank_article_candidates(registry_title, source_records)
    if not ranked:
        return {"status": "UNMATCHED", "match": None, "candidates": []}

    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    if top.score >= auto_accept and (
        second is None or top.score - second.score >= ambiguity_margin
    ):
        return {
            "status": "MATCHED",
            "match": top.source_path,
            "score": top.score,
            "candidates": [c.__dict__ for c in ranked],
        }
    return {
        "status": "REVIEW",
        "match": None,
        "score": top.score,
        "candidates": [c.__dict__ for c in ranked],
    }
