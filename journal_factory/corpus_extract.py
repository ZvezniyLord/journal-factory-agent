from __future__ import annotations

import re
import shutil
import subprocess
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from .corpus_utils import normalize_space, sha256_file, tokenize

WORD_RE = re.compile(r"[\w’'\-]+", re.UNICODE)
NON_ARTICLE_MARKERS = {
    "анкета", "заявка", "квитанц", "чек", "оплата", "рахунок", "invoice",
    "receipt", "payment", "сертиф", "certificate", "інформаційний лист",
    "информационное письмо", "договір", "contract", "фото", "паспорт",
}
ARTICLE_MARKERS = (
    "удк", "udc", "анотац", "abstract", "ключові слова", "keywords",
    "список використаних джерел", "references",
)


class ExtractionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExtractedDocument:
    path: str
    sha256: str
    size: int
    extension: str
    extraction_method: str
    text: str
    word_count: int
    is_article_candidate: bool
    rejection_reasons: tuple[str, ...]

    def to_record(self, *, include_text: bool = False) -> dict:
        row = asdict(self)
        if not include_text:
            row.pop("text", None)
        return row


def _xml_text(blob: bytes) -> str:
    try:
        root = ET.fromstring(blob)
    except ET.ParseError as exc:
        raise ExtractionError(f"XML_PARSE_FAILED:{exc}") from exc
    chunks: list[str] = []
    for elem in root.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag in {"t", "tab"}:
            if tag == "tab":
                chunks.append("\t")
            elif elem.text:
                chunks.append(elem.text)
        elif tag in {"p", "tr"}:
            chunks.append("\n")
    return "\n".join(x.strip() for x in "".join(chunks).splitlines() if x.strip())


def _extract_docx(path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            parts = ["word/document.xml"]
            parts += sorted(
                name for name in archive.namelist()
                if name.startswith("word/") and name.endswith(".xml")
                and ("footnote" in name or "endnote" in name)
            )
            text = "\n".join(_xml_text(archive.read(name)) for name in parts if name in archive.namelist())
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ExtractionError(f"DOCX_READ_FAILED:{exc}") from exc
    return text, "OOXML_XML"


def _extract_odt(path: Path) -> tuple[str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            return _xml_text(archive.read("content.xml")), "ODT_XML"
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ExtractionError(f"ODT_READ_FAILED:{exc}") from exc


def _extract_pdf(path: Path) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ExtractionError("PYPDF_NOT_INSTALLED") from exc
    try:
        reader = PdfReader(str(path), strict=False)
        return "\n\f\n".join(page.extract_text() or "" for page in reader.pages), "PYPDF"
    except Exception as exc:
        raise ExtractionError(f"PDF_TEXT_FAILED:{type(exc).__name__}:{exc}") from exc


def _extract_doc(path: Path) -> tuple[str, str]:
    if not shutil.which("antiword"):
        raise ExtractionError("ANTIWORD_NOT_AVAILABLE")
    proc = subprocess.run(
        ["antiword", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=180,
        check=False,
    )
    if proc.returncode != 0:
        raise ExtractionError(f"ANTIWORD_FAILED:{proc.returncode}:{proc.stderr[-300:]!r}")
    for encoding in ("utf-8", "cp1251", "cp1252"):
        try:
            return proc.stdout.decode(encoding), f"ANTIWORD_{encoding.upper()}"
        except UnicodeDecodeError:
            pass
    return proc.stdout.decode("utf-8", errors="replace"), "ANTIWORD_REPLACE"


def _extract_rtf(path: Path) -> tuple[str, str]:
    try:
        from striprtf.striprtf import rtf_to_text
    except ImportError as exc:
        raise ExtractionError("STRIPRTF_NOT_INSTALLED") from exc
    raw = path.read_text(encoding="utf-8", errors="replace")
    return rtf_to_text(raw), "STRIPRTF"


def _classify_candidate(path: Path, text: str) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    filename = path.name.casefold()
    for marker in NON_ARTICLE_MARKERS:
        if marker in filename:
            reasons.append(f"FILENAME_MARKER:{marker}")
    words = tokenize(text)
    lowered = text.casefold()
    marker_count = sum(marker in lowered for marker in ARTICLE_MARKERS)
    if len(words) < 120:
        reasons.append("TOO_FEW_WORDS")
    if marker_count == 0 and len(words) < 500:
        reasons.append("NO_ARTICLE_STRUCTURE_MARKER")
    return not reasons, tuple(reasons)


def extract_document(path: Path, *, display_path: str | None = None) -> ExtractedDocument:
    suffix = path.suffix.casefold()
    if suffix == ".docx":
        text, method = _extract_docx(path)
    elif suffix == ".doc":
        text, method = _extract_doc(path)
    elif suffix == ".odt":
        text, method = _extract_odt(path)
    elif suffix == ".rtf":
        text, method = _extract_rtf(path)
    elif suffix == ".pdf":
        text, method = _extract_pdf(path)
    elif suffix in {".txt", ".md"}:
        text, method = path.read_text(encoding="utf-8", errors="replace"), "UTF8_TEXT"
    else:
        raise ExtractionError(f"UNSUPPORTED_EXTENSION:{suffix}")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    is_candidate, reasons = _classify_candidate(path, text)
    return ExtractedDocument(
        path=display_path or str(path),
        sha256=sha256_file(path),
        size=path.stat().st_size,
        extension=suffix,
        extraction_method=method,
        text=text,
        word_count=len(tokenize(text)),
        is_article_candidate=is_candidate,
        rejection_reasons=reasons,
    )


def extract_tree(root: Path) -> tuple[list[ExtractedDocument], list[dict]]:
    supported = {".docx", ".doc", ".odt", ".rtf", ".pdf", ".txt", ".md"}
    documents: list[ExtractedDocument] = []
    failures: list[dict] = []
    for path in sorted(x for x in root.rglob("*") if x.is_file() and x.suffix.casefold() in supported):
        relative = str(path.relative_to(root))
        try:
            documents.append(extract_document(path, display_path=relative))
        except Exception as exc:
            failures.append({
                "path": relative,
                "status": "EXTRACTION_FAILED",
                "error": f"{type(exc).__name__}:{exc}",
            })
    return documents, failures
