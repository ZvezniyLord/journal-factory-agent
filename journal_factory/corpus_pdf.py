from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from .corpus_utils import normalize_space, sha256_file

UDC_RE = re.compile(r"^(?:UDC|УДК)\s*[:.]?\s*(.+)$", re.IGNORECASE)
ANNOTATION_RE = re.compile(
    r"^(?:Abstract|Анотац(?:ія|ії)|Аннотац(?:ия|ии)|Аңдатпа|Keywords|Ключові слова)\b",
    re.IGNORECASE,
)
ISBN_RE = re.compile(r"ISBN\s+([0-9\-Xx]+)")
DOI_RE = re.compile(r"(?:https?://doi\.org/)?(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)")


class GoldenParseError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoldenArticle:
    article_id: str
    ordinal: int
    physical_start_page: int
    physical_end_page: int
    printed_start_page: int | None
    section: str | None
    udc: str
    authors: tuple[str, ...]
    title: str
    header_lines: tuple[str, ...]
    body_preview: str

    def to_record(self) -> dict:
        return asdict(self)


def validate_pdf(path: Path) -> dict:
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise GoldenParseError("MISSING_PDF_MAGIC")
    if path.stat().st_size < 1024:
        raise GoldenParseError("PDF_TOO_SMALL")
    pages = None
    if shutil.which("pdfinfo"):
        process = subprocess.run(
            ["pdfinfo", str(path)], capture_output=True, text=True, timeout=120, check=False
        )
        if process.returncode != 0:
            raise GoldenParseError("PDFINFO_FAILED")
        for line in process.stdout.splitlines():
            if line.startswith("Pages:"):
                pages = int(line.split(":", 1)[1].strip())
    else:
        try:
            from pypdf import PdfReader
            pages = len(PdfReader(str(path), strict=False).pages)
        except Exception as exc:
            raise GoldenParseError(f"PDF_PAGE_COUNT_FAILED:{exc}") from exc
    if not pages:
        raise GoldenParseError("NO_PAGES")
    render_verified = False
    if shutil.which("pdftoppm"):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "probe"
            process = subprocess.run(
                ["pdftoppm", "-f", "1", "-singlefile", "-png", "-r", "36", str(path), str(output)],
                capture_output=True,
                timeout=180,
                check=False,
            )
            render_verified = process.returncode == 0 and output.with_suffix(".png").exists()
        if not render_verified:
            raise GoldenParseError("PDF_RENDER_FAILED")
    return {
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
        "pages": pages,
        "render_verified": render_verified,
    }


def _clean_lines(text: str) -> list[str]:
    return [normalize_space(line) for line in text.replace("\x00", "").splitlines() if normalize_space(line)]


def extract_pdf_pages(path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path), strict=False)
        return [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise GoldenParseError(f"PDF_EXTRACTION_FAILED:{type(exc).__name__}:{exc}") from exc


def publication_metadata(pages: list[str]) -> dict:
    front = "\n".join(pages[:4])
    isbn = ISBN_RE.search(front)
    dois = DOI_RE.findall(front)
    title_lines: list[str] = []
    for page_text in pages[:2]:
        lines = _clean_lines(page_text)
        publisher_index = next(
            (i for i, line in enumerate(lines) if "SCIENTIFIC AND PUBLISHING CENTER" in line.upper()), None
        )
        proceedings_index = next(
            (i for i, line in enumerate(lines) if "PROCEEDINGS OF THE" in line.upper()), None
        )
        if publisher_index is None or proceedings_index is None or proceedings_index <= publisher_index:
            continue
        candidate = lines[publisher_index + 1 : proceedings_index]
        candidate = [
            line for line in candidate
            if line.upper() == line
            and any(character.isalpha() for character in line)
            and not re.search(
                r"\b(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER)\b",
                line.upper(),
            )
        ]
        if candidate:
            title_lines = candidate
            break
    return {
        "title": normalize_space(" ".join(title_lines)) or None,
        "isbn": isbn.group(1) if isbn else None,
        "collection_doi": dois[0] if dois else None,
        "physical_page_count": len(pages),
    }


def _upper_ratio(value: str) -> float:
    letters = [character for character in value if character.isalpha()]
    return sum(character.isupper() for character in letters) / len(letters) if letters else 0.0


def _metadata_like(line: str) -> bool:
    lowered = line.casefold()
    markers = (
        "phd", "доктор", "кандидат", "магістр", "аспірант", "здобувач",
        "професор", "доцент", "викладач", "кафедр", "університет", "інститут",
        "академ", "м. ", "ukraine", "україна", "orcid", "email", "@",
    )
    return any(marker in lowered for marker in markers)


def _name_like(line: str) -> bool:
    if _metadata_like(line) or len(line) > 140:
        return False
    tokens = [token.strip(",.;:") for token in line.split()]
    alpha = [token for token in tokens if any(character.isalpha() for character in token)]
    if not 2 <= len(alpha) <= 12:
        return False
    capitals = sum(token[:1].isupper() for token in alpha)
    return capitals / len(alpha) >= 0.7 and _upper_ratio(line) < 0.85


def _printed_page(lines: list[str]) -> int | None:
    candidates = lines[:6] + list(reversed(lines[-12:]))
    for line in candidates:
        match = re.fullmatch(r"(?:.*?\D)?(\d{1,4})", line)
        if match and len(line) <= 12:
            return int(match.group(1))
    return None


def _parse_header(lines: list[str], udc_index: int) -> tuple[tuple[str, ...], str, str]:
    tail = lines[udc_index + 1 :]
    explicit_marker = next((i for i, line in enumerate(tail[:60]) if ANNOTATION_RE.match(line)), None)
    header_limit = explicit_marker if explicit_marker is not None else min(len(tail), 35)
    header = tail[:header_limit]
    if not header:
        return (), "", ""
    title_start = next(
        (
            index for index, line in enumerate(header)
            if _upper_ratio(line) >= 0.72 and len(line) >= 8 and not _metadata_like(line)
        ),
        None,
    )
    if title_start is None:
        return tuple(line.rstrip(",.;") for line in header[:5] if _name_like(line)), "", ""
    title_end = title_start
    while title_end < len(header):
        line = header[title_end]
        if _upper_ratio(line) < 0.52 and title_end > title_start:
            break
        if _metadata_like(line) and title_end > title_start:
            break
        title_end += 1
    title = normalize_space(" ".join(header[title_start:title_end]))
    authors = tuple(line.rstrip(",.;") for line in header[:title_start] if _name_like(line))
    body_start = explicit_marker if explicit_marker is not None else title_end
    preview = normalize_space(" ".join(tail[body_start : body_start + 18]))
    return authors, title, preview


def parse_golden_pages(pages: list[str], conference_id: int) -> tuple[dict, list[GoldenArticle], list[dict]]:
    starts: list[dict] = []
    warnings: list[dict] = []
    toc_start = next((index for index, text in enumerate(pages) if "TABLE OF CONTENTS" in text.upper()), None)
    scan_from = toc_start + 1 if toc_start is not None else 0
    for page_index, text in enumerate(pages):
        if page_index < scan_from:
            continue
        lines = _clean_lines(text)
        matches = [(index, UDC_RE.match(line)) for index, line in enumerate(lines) if UDC_RE.match(line)]
        if not matches:
            continue
        index, match = matches[0]
        if index > 18:
            warnings.append({"page": page_index + 1, "code": "LATE_UDC_IGNORED", "line": lines[index]})
            continue
        before = [line for line in lines[:index] if not re.fullmatch(r"\d+", line)]
        section = normalize_space(" ".join(before[-3:])) if before else None
        authors, title, preview = _parse_header(lines, index)
        if not title:
            warnings.append({"page": page_index + 1, "code": "TITLE_NOT_DETECTED"})
        starts.append({
            "physical_start_page": page_index + 1,
            "printed_start_page": _printed_page(lines),
            "section": section,
            "udc": match.group(1).strip() if match else "",
            "authors": authors,
            "title": title,
            "header_lines": tuple(lines[index + 1 : index + 36]),
            "body_preview": preview,
        })
    articles: list[GoldenArticle] = []
    for ordinal, start in enumerate(starts, 1):
        end = starts[ordinal]["physical_start_page"] - 1 if ordinal < len(starts) else len(pages)
        articles.append(GoldenArticle(
            article_id=f"c{conference_id:03d}-a{ordinal:03d}",
            ordinal=ordinal,
            physical_start_page=start["physical_start_page"],
            physical_end_page=end,
            printed_start_page=start["printed_start_page"],
            section=start["section"],
            udc=start["udc"],
            authors=start["authors"],
            title=start["title"],
            header_lines=start["header_lines"],
            body_preview=start["body_preview"],
        ))
    return publication_metadata(pages), articles, warnings


def parse_golden_pdf(path: Path, conference_id: int) -> tuple[dict, list[GoldenArticle], list[dict]]:
    return parse_golden_pages(extract_pdf_pages(path), conference_id)
