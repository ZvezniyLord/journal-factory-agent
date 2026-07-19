from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import json
import re
import unicodedata

from rapidfuzz.fuzz import ratio, token_set_ratio

from .archive_workspace import sha256_file
from .corpus_pdf import extract_pdf_pages, parse_golden_pages


ARTICLE_RE = re.compile(r"^(\d{1,3})\.\s+(.+)$")
PAGE_RE = re.compile(r"^\d{1,4}$")
SPECIAL_THANKS_START = "SPECIAL THANKS FOR ACTIVE PARTICIPATION"


def extract_official_toc(
    pdf_path: Path,
    conference_id: int,
    *,
    expected_articles: int | None = None,
    expected_sections: int | None = None,
    source_url: str = "",
) -> dict[str, Any]:
    pages = extract_pdf_pages(pdf_path)
    toc = parse_official_toc_pages(pages)
    publication, body_articles, body_warnings = parse_golden_pages(pages, conference_id)
    blockers = list(toc["blockers"])
    warnings = list(toc["warnings"])

    if expected_articles is not None and len(toc["articles"]) != expected_articles:
        blockers.append(
            f"official_toc_article_count:{len(toc['articles'])}:expected={expected_articles}"
        )
    if expected_sections is not None and len(toc["sections"]) != expected_sections:
        blockers.append(
            f"official_toc_section_count:{len(toc['sections'])}:expected={expected_sections}"
        )
    if len(body_articles) != len(toc["articles"]):
        blockers.append(
            f"official_body_article_count:{len(body_articles)}:toc={len(toc['articles'])}"
        )

    offsets: list[int] = []
    for index, entry in enumerate(toc["articles"]):
        if index >= len(body_articles):
            break
        body = body_articles[index]
        entry["physical_start_page"] = body.physical_start_page
        entry["physical_end_page"] = body.physical_end_page
        offsets.append(body.physical_start_page - int(entry["printed_start_page"]))
        if body.title:
            title_score = _text_similarity(entry["title"], body.title)
            entry["body_title_score"] = round(title_score, 6)
            if title_score < 0.68:
                warnings.append(
                    {
                        "code": "TOC_BODY_TITLE_REVIEW",
                        "ordinal": entry["ordinal"],
                        "score": round(title_score, 6),
                    }
                )
        else:
            entry["body_title_score"] = 0.0
            warnings.append(
                {"code": "BODY_TITLE_NOT_DETECTED", "ordinal": entry["ordinal"]}
            )

    unique_offsets = sorted(set(offsets))
    if len(unique_offsets) != 1:
        blockers.append(
            "physical_printed_offsets_not_constant:"
            + ",".join(str(value) for value in unique_offsets)
        )
    offset = unique_offsets[0] if len(unique_offsets) == 1 else None
    page_numbering = {
        "physical_to_printed_offset": offset,
        "first_numbered_physical_page": offset + 1 if offset is not None else None,
        "first_printed_page": 1 if offset is not None else None,
        "numbered_section_index": 2,
        "hide_numbers_before_numbered_section": True,
    }
    identity = {
        "source_url": source_url,
        "sha256": sha256_file(pdf_path),
        "size_bytes": pdf_path.stat().st_size,
        "physical_page_count": len(pages),
        "bibliographic_page_count": _bibliographic_page_count(pages),
        "title": publication.get("title"),
        "isbn": publication.get("isbn"),
        "collection_doi": publication.get("collection_doi"),
    }
    blockers = list(dict.fromkeys(blockers))
    return {
        "schema_version": 1,
        "conference_id": conference_id,
        "status": "PASS" if not blockers else "REVIEW",
        "extractor": "OFFICIAL_TOC_V1",
        "source": identity,
        "toc_physical_start_page": toc["toc_physical_start_page"],
        "toc_physical_end_page": toc["toc_physical_end_page"],
        "article_count": len(toc["articles"]),
        "section_count": len(toc["sections"]),
        "sections": toc["sections"],
        "articles": toc["articles"],
        "special_thanks": toc["special_thanks"],
        "page_numbering": page_numbering,
        "body_parser_warnings": body_warnings,
        "warnings": warnings,
        "blockers": blockers,
    }


def parse_official_toc_pages(pages: list[str]) -> dict[str, Any]:
    toc_start = next(
        (index for index, text in enumerate(pages) if "TABLE OF CONTENTS" in text.upper()),
        None,
    )
    if toc_start is None:
        return {
            "toc_physical_start_page": None,
            "toc_physical_end_page": None,
            "articles": [],
            "sections": [],
            "special_thanks": {"present": False},
            "warnings": [],
            "blockers": ["official_toc_heading_missing"],
        }

    stream: list[tuple[int, str]] = []
    toc_end = toc_start
    for page_index in range(toc_start, len(pages)):
        lines = _clean_lines(pages[page_index])
        if page_index > toc_start and _body_page_started(lines):
            break
        if lines and PAGE_RE.fullmatch(lines[0]):
            lines = lines[1:]
        if page_index == toc_start:
            heading = next(
                (index for index, line in enumerate(lines) if line.upper() == "TABLE OF CONTENTS"),
                None,
            )
            lines = lines[(heading + 1) if heading is not None else 0 :]
        stream.extend((page_index + 1, line) for line in lines)
        toc_end = page_index
        if any(line.upper().startswith(SPECIAL_THANKS_START) for line in lines):
            break

    articles: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    blockers: list[str] = []
    warnings: list[dict[str, Any]] = []
    current_section = ""
    pending_section: list[str] = []
    special_lines: list[tuple[int, str]] = []
    index = 0
    while index < len(stream):
        physical_page, line = stream[index]
        if line.upper().startswith(SPECIAL_THANKS_START):
            special_lines = stream[index:]
            break
        article_match = ARTICLE_RE.match(line)
        if article_match is None:
            if not PAGE_RE.fullmatch(line) and line.upper() != "TABLE OF CONTENTS":
                pending_section.append(line)
            index += 1
            continue

        ordinal = int(article_match.group(1))
        if pending_section:
            current_section = _join_wrapped(pending_section)
            if not sections or sections[-1]["title"] != current_section:
                sections.append(
                    {
                        "ordinal": len(sections) + 1,
                        "title": current_section,
                        "first_article_ordinal": ordinal,
                    }
                )
            pending_section = []
        if not current_section:
            blockers.append(f"official_toc_section_missing:{ordinal}")

        author_lines = [article_match.group(2)]
        index += 1
        while index < len(stream):
            _, candidate = stream[index]
            if _title_line(candidate):
                break
            if ARTICLE_RE.match(candidate) or PAGE_RE.fullmatch(candidate):
                break
            author_lines.append(candidate)
            index += 1

        title_lines: list[str] = []
        while index < len(stream):
            _, candidate = stream[index]
            if PAGE_RE.fullmatch(candidate):
                break
            if ARTICLE_RE.match(candidate) or candidate.upper().startswith(SPECIAL_THANKS_START):
                break
            title_lines.append(candidate)
            index += 1
        if index >= len(stream) or not PAGE_RE.fullmatch(stream[index][1]):
            blockers.append(f"official_toc_page_missing:{ordinal}")
            printed_page = None
        else:
            printed_page = int(stream[index][1])
            index += 1
        if not title_lines:
            blockers.append(f"official_toc_title_missing:{ordinal}")

        authors_display = _join_wrapped(author_lines)
        title = _join_wrapped(title_lines)
        articles.append(
            {
                "ordinal": ordinal,
                "section": current_section,
                "authors": _split_authors(authors_display),
                "authors_display": authors_display,
                "title": title,
                "printed_start_page": printed_page,
                "toc_physical_page": physical_page,
            }
        )

    expected_ordinals = list(range(1, len(articles) + 1))
    observed_ordinals = [int(item["ordinal"]) for item in articles]
    if observed_ordinals != expected_ordinals:
        blockers.append(
            "official_toc_ordinals_not_contiguous:"
            + ",".join(str(value) for value in observed_ordinals)
        )
    special = _parse_special_thanks(special_lines)
    if not special["present"]:
        warnings.append({"code": "SPECIAL_THANKS_NOT_FOUND"})
    return {
        "toc_physical_start_page": toc_start + 1,
        "toc_physical_end_page": toc_end + 1,
        "articles": articles,
        "sections": sections,
        "special_thanks": special,
        "warnings": warnings,
        "blockers": blockers,
    }


def resolve_publication_order(
    manifest: dict[str, Any],
    official_toc: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_articles = manifest.get("articles") or []
    official_articles = official_toc.get("articles") or []
    used: set[str] = set()
    mappings: list[dict[str, Any]] = []
    ambiguous: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    ordered: list[dict[str, Any]] = []

    for official in official_articles:
        ranked = sorted(
            (_score_manifest_article(official, candidate) for candidate in source_articles),
            key=lambda item: item["score"],
            reverse=True,
        )
        available = [row for row in ranked if row["source_key"] not in used]
        best = available[0] if available else None
        second = available[1] if len(available) > 1 else None
        if best is None:
            missing.append({"ordinal": official["ordinal"], "title": official["title"]})
            continue
        gap = best["score"] - (second["score"] if second else 0.0)
        exact_title = best["title_score"] >= 0.995
        author_supported = best["author_score"] >= 0.52
        accepted = (
            best["title_score"] >= 0.92
            and gap >= 0.025
            and (author_supported or exact_title)
        )
        mapping = {
            "official_ordinal": official["ordinal"],
            "official_section": official["section"],
            "official_title": official["title"],
            "official_authors": official["authors"],
            "official_printed_start_page": official["printed_start_page"],
            "official_physical_start_page": official.get("physical_start_page"),
            "source_article_id": best["article"].get("article_id"),
            "source_journal_order": best["article"].get("journal_order"),
            "source_path": best["article"].get("source_path"),
            "source_sha256": best["article"].get("source_sha256"),
            "title_score": round(best["title_score"], 6),
            "author_score": round(best["author_score"], 6),
            "score": round(best["score"], 6),
            "candidate_gap": round(gap, 6),
            "status": "MATCHED" if accepted else "AMBIGUOUS",
            "alternatives": [
                {
                    "article_id": row["article"].get("article_id"),
                    "journal_order": row["article"].get("journal_order"),
                    "title_score": round(row["title_score"], 6),
                    "author_score": round(row["author_score"], 6),
                    "score": round(row["score"], 6),
                }
                for row in available[:3]
            ],
        }
        mappings.append(mapping)
        if not accepted:
            ambiguous.append(mapping)
            continue

        used.add(best["source_key"])
        article = deepcopy(best["article"])
        original_id = str(article.get("article_id") or "")
        original_order = article.get("journal_order")
        ordinal = int(official["ordinal"])
        article["inventory_article_id"] = original_id
        article["participant_order"] = original_order
        article["article_id"] = f"article-{ordinal:03d}"
        article["journal_order"] = ordinal
        article["section_id"] = official["section"]
        article["section_raw"] = official["section"]
        article["title_official"] = official["title"]
        article["authors_official"] = official["authors"]
        article["official_printed_start_page"] = official["printed_start_page"]
        article["official_physical_start_page"] = official.get("physical_start_page")
        article["publication_evidence"] = {
            "extractor": official_toc.get("extractor"),
            "official_pdf_sha256": official_toc.get("source", {}).get("sha256"),
            "title_score": mapping["title_score"],
            "author_score": mapping["author_score"],
            "source_article_id": original_id,
            "source_journal_order": original_order,
        }
        ordered.append(article)

    extras = [
        {
            "article_id": article.get("article_id"),
            "journal_order": article.get("journal_order"),
            "title": article.get("title_manifest") or article.get("title_detected"),
        }
        for article in source_articles
        if _source_key(article) not in used
    ]
    original_order = [mapping["source_journal_order"] for mapping in mappings]
    order_was_already_official = original_order == list(range(1, len(official_articles) + 1))
    section_titles = list(dict.fromkeys(item["section"] for item in official_articles))
    blockers = []
    if missing:
        blockers.append(f"official_missing:{len(missing)}")
    if extras:
        blockers.append(f"raw_extra:{len(extras)}")
    if ambiguous:
        blockers.append(f"ambiguous:{len(ambiguous)}")
    if len(ordered) != len(official_articles):
        blockers.append(
            f"matched_count:{len(ordered)}:official={len(official_articles)}"
        )
    report = {
        "schema_version": 1,
        "status": "PASS" if not blockers else "REVIEW",
        "resolver": "PUBLICATION_ORDER_V1",
        "official_pdf_sha256": official_toc.get("source", {}).get("sha256"),
        "official_article_count": len(official_articles),
        "raw_article_count": len(source_articles),
        "matched_count": len(ordered),
        "missing": missing,
        "extra": extras,
        "ambiguous": ambiguous,
        "missing_count": len(missing),
        "extra_count": len(extras),
        "ambiguous_count": len(ambiguous),
        "official_section_count": len(section_titles),
        "official_sections": section_titles,
        "source_order_was_publication_order": order_was_already_official,
        "official_order_matches": not blockers,
        "official_sections_match": not blockers,
        "mappings": mappings,
        "blockers": blockers,
    }
    updated = deepcopy(manifest)
    updated["articles"] = ordered
    updated["article_count"] = len(ordered)
    updated["generation_mode"] = (
        str(updated.get("generation_mode") or "UNKNOWN") + "+PUBLICATION_ORDER_V1"
    )
    updated["publication_order_report"] = "official_corpus_parity.json"
    updated["manifest_status"] = "PASS" if not blockers else "BLOCKED"
    if blockers:
        updated["blockers"] = [*updated.get("blockers", []), *blockers]
    return updated, report


def load_official_toc(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("official_toc_schema_version_must_equal_1")
    if payload.get("status") != "PASS":
        raise ValueError("official_toc_status_must_be_PASS")
    if not isinstance(payload.get("articles"), list) or not payload["articles"]:
        raise ValueError("official_toc_articles_missing")
    if not isinstance(payload.get("sections"), list) or not payload["sections"]:
        raise ValueError("official_toc_sections_missing")
    return payload


def _clean_lines(text: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", line.replace("\x00", "")).strip()
        for line in text.splitlines()
        if line.strip()
    ]


def _body_page_started(lines: list[str]) -> bool:
    return any(re.match(r"^(?:UDC|УДК)\b", line, flags=re.IGNORECASE) for line in lines[:18])


def _upper_ratio(value: str) -> float:
    letters = [character for character in value if character.isalpha()]
    return sum(character.isupper() for character in letters) / len(letters) if letters else 0.0


def _title_line(value: str) -> bool:
    return len(value) >= 5 and _upper_ratio(value) >= 0.82


def _join_wrapped(lines: list[str]) -> str:
    value = " ".join(line.strip() for line in lines if line.strip())
    value = re.sub(r"-\s+(?=\w)", "-", value)
    return re.sub(r"\s+", " ", value).strip()


def _split_authors(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_special_thanks(lines: list[tuple[int, str]]) -> dict[str, Any]:
    if not lines:
        return {"present": False}
    heading_lines: list[str] = []
    participant_lines: list[str] = []
    heading_complete = False
    for _, line in lines:
        if not heading_complete:
            heading_lines.append(line)
            heading_complete = line.rstrip().endswith(":")
        else:
            participant_lines.append(line)
    heading = _join_wrapped(heading_lines)
    participants_display = _join_wrapped(participant_lines)
    participants = [_repair_split_surname(item) for item in _split_authors(participants_display)]
    return {
        "present": bool(heading and participants_display),
        "heading": heading,
        "participants": participants,
        "participants_display": ", ".join(participants),
        "physical_page": lines[0][0],
    }


def _repair_split_surname(value: str) -> str:
    parts = value.split()
    if len(parts) == 3 and len(parts[-1]) <= 2 and 2 <= len(parts[-2]) <= 3:
        return f"{parts[0]} {parts[1]}{parts[2]}"
    return value


def _bibliographic_page_count(pages: list[str]) -> int | None:
    front = "\n".join(pages[:4])
    matches = re.findall(r"(?:-|–)\s*(\d{2,4})\s*p\.", front, flags=re.IGNORECASE)
    return int(matches[-1]) if matches else None


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("’", "'").replace("`", "'")
    value = re.sub(r"-\s+", "-", value)
    return re.sub(r"[^\w]+", " ", value).strip()


def _text_similarity(left: str, right: str) -> float:
    a, b = _normalize(left), _normalize(right)
    if not a or not b:
        return 0.0
    return max(ratio(a, b), token_set_ratio(a, b)) / 100.0


def _transliterate(value: str) -> str:
    table = str.maketrans(
        {
            "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d",
            "е": "e", "є": "ie", "ж": "zh", "з": "z", "и": "y", "і": "i",
            "ї": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n",
            "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
            "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
            "ь": "", "ю": "iu", "я": "ia", "ы": "y", "э": "e", "ъ": "",
        }
    )
    return _normalize(value).translate(table)


def _author_similarity(official: list[str], candidate: list[str]) -> float:
    if not official or not candidate:
        return 0.0
    normalized_candidate = [_transliterate(value) for value in candidate if value]
    scores = []
    for author in official:
        normalized = _transliterate(author)
        scores.append(
            max(
                (_text_similarity(normalized, item) for item in normalized_candidate),
                default=0.0,
            )
        )
    return sum(scores) / len(scores) if scores else 0.0


def _score_manifest_article(official: dict[str, Any], article: dict[str, Any]) -> dict[str, Any]:
    titles = [
        str(article.get("title_manifest") or ""),
        str(article.get("title_detected") or ""),
    ]
    title_score = max(
        (_text_similarity(str(official.get("title") or ""), title) for title in titles if title),
        default=0.0,
    )
    authors = [
        str(value)
        for field in ("authors_manifest", "authors_detected")
        for value in (article.get(field) or [])
        if value
    ]
    author_score = _author_similarity(official.get("authors") or [], authors)
    score = 0.85 * title_score + 0.15 * author_score
    return {
        "article": article,
        "source_key": _source_key(article),
        "title_score": title_score,
        "author_score": author_score,
        "score": score,
    }


def _source_key(article: dict[str, Any]) -> str:
    return str(article.get("source_sha256") or article.get("source_path") or article.get("article_id"))
