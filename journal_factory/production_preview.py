from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from xml.etree import ElementTree as ET

import requests
from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.shared import Pt
from docxcompose.composer import Composer
from PIL import Image, ImageDraw

from .config import AppConfig


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


@dataclass(frozen=True)
class ArticleCandidate:
    article_id: str
    source_path: str
    extracted_path: Path
    source_sha256: str
    title: str
    has_udc: bool
    table_count: int
    image_hashes: list[str]
    reference_count: int
    paragraph_count: int
    normalized_text: str
    score: int


def run_production_preview(config: AppConfig, limit: int = 3) -> dict[str, Any]:
    build_dir = config.build_dir
    reports_dir = build_dir / "reports"
    render_dir = build_dir / "render"
    workspace_dir = build_dir / "workspace"
    for path in (reports_dir, render_dir, workspace_dir):
        path.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="journal-preview-") as tmp:
        source_root = Path(tmp) / "source"
        _materialize_source(config.archive, source_root)
        candidates = _discover_article_candidates(source_root)
        selected = _select_smoke_articles(candidates, limit)
        if not selected:
            audit = {
                "status": "REVIEW",
                "result": "NO_ARTICLES_SELECTED",
                "articles": [],
                "warnings": ["No readable DOCX article candidates found."],
            }
            _write_json(reports_dir / "SMOKE_AUDIT.json", audit)
            return {"status": "REVIEW", "articles": 0, "audit": str(reports_dir / "SMOKE_AUDIT.json")}

        output_docx = build_dir / "JOURNAL_SMOKE.docx"
        output_pdf = build_dir / "JOURNAL_SMOKE.pdf"
        gemma_decisions = _collect_udc_decisions(selected)
        _assemble_smoke_docx(config.etalon, output_docx, selected, gemma_decisions)
        final_doc = Document(str(output_docx))
        article_audits = [_audit_article(candidate, output_docx, index) for index, candidate in enumerate(selected, start=1)]
        _render_pdf_and_pages(output_docx, output_pdf, render_dir)
        contact_sheet = _make_contact_sheet(render_dir)

        warnings = []
        failures = []
        for item in article_audits:
            failures.extend(item["failures"])
            warnings.extend(item["warnings"])
        if any("Р" in item["source_path"] or "Р" in item["title"] for item in article_audits):
            warnings.append("audit_filename_or_title_encoding_mojibake")
        if not output_pdf.exists():
            failures.append("pdf_render_missing")
        if not contact_sheet.exists():
            failures.append("contact_sheet_missing")

        audit = {
            "status": "REVIEW" if not failures else "FAIL",
            "pass_forbidden": True,
            "mode": "production-preview",
            "docx": str(output_docx),
            "pdf": str(output_pdf),
            "render_dir": str(render_dir),
            "contact_sheet": str(contact_sheet),
            "article_count": len(selected),
            "articles": article_audits,
        "gemma": gemma_decisions,
        "gemma_note": "No selected real article lacked literal UDC; no UDC proposal was requested."
        if not gemma_decisions
        else "UDC proposal requested only for selected articles without literal UDC.",
            "visible_defects": failures + warnings,
            "final_paragraph_count": len(final_doc.paragraphs),
            "final_table_count": len(final_doc.tables),
        }
        _write_json(reports_dir / "SMOKE_AUDIT.json", audit)
        return {
            "status": "REVIEW",
            "articles": len(selected),
            "docx": str(output_docx),
            "pdf": str(output_pdf),
            "contact_sheet": str(contact_sheet),
            "audit": str(reports_dir / "SMOKE_AUDIT.json"),
            "visible_defects": audit["visible_defects"],
        }


def _materialize_source(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
        return
    if not zipfile.is_zipfile(source):
        raise ValueError(f"Source must be a ZIP or directory: {source}")
    with zipfile.ZipFile(source) as archive:
        root = destination.resolve()
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"Blocked unsafe ZIP member: {member.filename}")
            archive.extract(member, destination)


def _discover_article_candidates(source_root: Path) -> list[ArticleCandidate]:
    candidates = []
    for path in sorted(source_root.rglob("*.docx")):
        if _is_service_file(path):
            continue
        rel = _repair_mojibake(path.relative_to(source_root).as_posix())
        lower = path.name.lower()
        if any(token in lower for token in ("анкета", "anketa", "заяв", "оплат", "oplata", "квитан", "сертиф", "інформаційний лист")):
            continue
        try:
            info = _inspect_docx(path)
        except Exception:
            continue
        if not info["normalized_text"]:
            continue
        feature_score = (
            info["table_count"] * 5
            + len(info["image_hashes"]) * 5
            + min(info["reference_count"], 5)
            + (4 if not info["has_udc"] else 0)
        )
        candidates.append(
            ArticleCandidate(
                article_id=f"article-{len(candidates) + 1:03d}",
                source_path=rel,
                extracted_path=path,
                source_sha256=_sha256_file(path),
                title=_repair_mojibake(info["title"]),
                has_udc=info["has_udc"],
                table_count=info["table_count"],
                image_hashes=info["image_hashes"],
                reference_count=info["reference_count"],
                paragraph_count=info["paragraph_count"],
                normalized_text=info["normalized_text"],
                score=feature_score,
            )
        )
    return candidates


def _select_smoke_articles(candidates: list[ArticleCandidate], limit: int) -> list[ArticleCandidate]:
    selected: list[ArticleCandidate] = []

    def add(predicate) -> None:
        if len(selected) >= limit:
            return
        for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
            if candidate in selected:
                continue
            if predicate(candidate):
                selected.append(candidate)
                return

    add(lambda item: item.table_count > 0)
    add(lambda item: len(item.image_hashes) > 0)
    add(lambda item: item.reference_count > 0 and not item.has_udc)
    add(lambda item: item.reference_count > 0)
    for candidate in sorted(candidates, key=lambda item: item.score, reverse=True):
        if len(selected) >= limit:
            break
        if candidate not in selected:
            selected.append(candidate)
    return selected[:limit]


def _assemble_smoke_docx(
    etalon: Path,
    output_docx: Path,
    selected: list[ArticleCandidate],
    gemma_decisions: list[dict[str, Any]],
) -> None:
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(etalon, output_docx)
    base = Document(str(output_docx))
    _add_toc_page(base, selected)
    base.save(str(output_docx))

    master = Document(str(output_docx))
    composer = Composer(master)
    for index, candidate in enumerate(selected, start=1):
        marker_doc = Document()
        marker_doc.add_page_break()
        p = marker_doc.add_paragraph(f"SMOKE ARTICLE {index}: {candidate.title}")
        _safe_style(p, "SECTION")
        marker_doc.add_paragraph("")
        composer.append(marker_doc)
        composer.append(Document(str(candidate.extracted_path)))
    composer.save(str(output_docx))
    _apply_smoke_styles(output_docx, selected)


def _add_toc_page(doc: Document, selected: list[ArticleCandidate]) -> None:
    doc.add_page_break()
    title = doc.add_paragraph("ЗМІСТ")
    _safe_style(title, "SECTION")
    for index, candidate in enumerate(selected, start=1):
        row = doc.add_paragraph(f"{index}. {candidate.title}")
        _safe_style(row, "pip")


def _apply_smoke_styles(output_docx: Path, selected: list[ArticleCandidate]) -> None:
    doc = Document(str(output_docx))
    known_titles = {candidate.title for candidate in selected}
    in_references = False
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        lower = text.lower()
        if text.startswith("SMOKE ARTICLE"):
            _safe_style(paragraph, "SECTION")
            in_references = False
        elif text in known_titles or _looks_like_title(text):
            _safe_style(paragraph, "Назва1")
        elif re.match(r"^(удк|уdc|udc)\b", lower, flags=re.IGNORECASE):
            _safe_style(paragraph, "UDC")
        elif _looks_like_references_title(text):
            _safe_style(paragraph, "REF-TITLE")
            in_references = True
        elif in_references:
            _safe_style(paragraph, "REFER")
        elif _looks_like_figure_caption(text):
            _safe_style(paragraph, "РисПід")
        elif _looks_like_table_caption(text):
            _safe_style(paragraph, "РИС")
        elif _looks_like_author_line(text):
            _safe_style(paragraph, "AUTOR")
        else:
            _safe_style(paragraph, "pip")
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _safe_style(paragraph, "TABLETEXT")
    doc.save(str(output_docx))


def _audit_article(candidate: ArticleCandidate, final_docx: Path, index: int) -> dict[str, Any]:
    final_info = _inspect_docx(final_docx)
    source_text = candidate.normalized_text
    text_found = _normalized_contains(final_info["normalized_text"], source_text)
    source_media = set(candidate.image_hashes)
    final_media = set(final_info["image_hashes"])
    missing_media = sorted(source_media - final_media)
    failures = []
    warnings = ["business_normalization_incomplete_review"]
    if not text_found:
        failures.append("text_not_fully_found_in_final")
    if candidate.table_count > final_info["table_count"]:
        failures.append("table_count_loss")
    if missing_media:
        failures.append("media_hash_missing")
    if candidate.reference_count and candidate.reference_count > final_info["reference_count"]:
        failures.append("references_count_loss")
    style_ids = _collect_style_ids(final_docx)
    return {
        "article_id": candidate.article_id,
        "journal_order": index,
        "source_path": candidate.source_path,
        "source_sha256": candidate.source_sha256,
        "title": candidate.title,
        "source_meaningful_paragraphs": candidate.paragraph_count,
        "source_tables": candidate.table_count,
        "source_media_count": len(candidate.image_hashes),
        "source_media_sha256": candidate.image_hashes,
        "source_references": candidate.reference_count,
        "normalized_text_found_in_final": text_found,
        "final_tables_total": final_info["table_count"],
        "final_media_sha256": final_info["image_hashes"],
        "final_references_total": final_info["reference_count"],
        "actual_style_ids": style_ids,
        "starts_on_new_page": True,
        "warnings": warnings,
        "failures": failures,
        "status": "FAIL" if failures else "REVIEW",
    }


def _collect_udc_decisions(selected: list[ArticleCandidate]) -> list[dict[str, Any]]:
    decisions = []
    for candidate in selected:
        if candidate.has_udc:
            continue
        decisions.append(_ask_gemma_udc(candidate))
    return decisions


def _ask_gemma_udc(candidate: ArticleCandidate) -> dict[str, Any]:
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/")
    model = "gemma2:2b"
    prompt = {
        "instruction": "Return only valid JSON with a cautious UDC proposal. Do not write prose.",
        "schema": {
            "decision_type": "udc_proposal",
            "article_id": candidate.article_id,
            "status": "needs_operator_review",
            "value": "",
            "confidence": 0.0,
            "evidence": [],
            "model": model,
            "prompt_version": "udc-smoke-v1",
            "source_hash": candidate.source_sha256,
        },
        "title": candidate.title,
        "text_excerpt": candidate.normalized_text[:2000],
    }
    fallback = {
        "decision_type": "udc_proposal",
        "article_id": candidate.article_id,
        "status": "model_unavailable",
        "value": "",
        "confidence": 0.0,
        "evidence": [],
        "model": model,
        "prompt_version": "udc-smoke-v1",
        "source_hash": candidate.source_sha256,
        "raw_response": "",
        "valid_json": False,
    }
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": json.dumps(prompt, ensure_ascii=False), "stream": False, "format": "json"},
            timeout=120,
        )
        response.raise_for_status()
        raw = response.json().get("response", "")
        parsed = json.loads(raw)
    except Exception as exc:
        fallback["error"] = str(exc)
        return fallback
    required = {
        "decision_type": "udc_proposal",
        "article_id": candidate.article_id,
        "status": "needs_operator_review",
        "model": model,
        "prompt_version": "udc-smoke-v1",
        "source_hash": candidate.source_sha256,
    }
    valid = isinstance(parsed, dict) and all(parsed.get(key) == value for key, value in required.items())
    valid = valid and isinstance(parsed.get("evidence"), list) and isinstance(parsed.get("confidence"), (int, float))
    parsed["raw_response"] = raw
    parsed["valid_json"] = bool(valid)
    if not valid:
        parsed["status"] = "invalid_model_json"
    return parsed


def _render_pdf_and_pages(output_docx: Path, output_pdf: Path, render_dir: Path) -> None:
    render_dir.mkdir(parents=True, exist_ok=True)
    for old_png in render_dir.glob("page-*.png"):
        old_png.unlink()
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(output_pdf.parent), str(output_docx)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=180,
    )
    generated_pdf = output_docx.with_suffix(".pdf")
    if generated_pdf.exists() and generated_pdf != output_pdf:
        shutil.move(str(generated_pdf), str(output_pdf))
    pdftoppm = shutil.which("pdftoppm")
    if output_pdf.exists() and pdftoppm:
        subprocess.run(
            [pdftoppm, "-png", "-r", "120", str(output_pdf), str(render_dir / "page")],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=180,
        )


def _make_contact_sheet(render_dir: Path) -> Path:
    pages = sorted(render_dir.glob("page-*.png"))
    output = render_dir / "contact_sheet.png"
    if not pages:
        return output
    thumbs = []
    for page in pages:
        image = Image.open(page).convert("RGB")
        image.thumbnail((360, 510))
        thumbs.append((page.name, image.copy()))
    width = 760
    cell_w = 380
    cell_h = 560
    rows = (len(thumbs) + 1) // 2
    sheet = Image.new("RGB", (width, max(1, rows) * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (name, image) in enumerate(thumbs):
        x = (i % 2) * cell_w + 10
        y = (i // 2) * cell_h + 30
        draw.text((x, y - 24), name, fill="black")
        sheet.paste(image, (x, y))
    sheet.save(output)
    return output


def _inspect_docx(path: Path) -> dict[str, Any]:
    doc = Document(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    table_cells = []
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = _normalize_text(cell.text)
                if text:
                    table_cells.append(text)
    with zipfile.ZipFile(path) as package:
        media_hashes = sorted(
            hashlib.sha256(package.read(name)).hexdigest()
            for name in package.namelist()
            if name.startswith("word/media/")
        )
    full_text = "\n".join(paragraphs + table_cells)
    refs = _count_references(paragraphs)
    return {
        "title": _repair_mojibake(_detect_title(paragraphs, path)),
        "has_udc": any(re.match(r"^(удк|уdc|udc)\b", p, re.IGNORECASE) for p in paragraphs[:10]),
        "table_count": len(doc.tables),
        "image_hashes": media_hashes,
        "reference_count": refs,
        "paragraph_count": len(paragraphs),
        "normalized_text": _normalize_text(_repair_mojibake(full_text)),
    }


def _collect_style_ids(path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    with zipfile.ZipFile(path) as package:
        xml = package.read("word/document.xml")
    root = ET.fromstring(xml)
    for p_style in root.findall(".//w:pStyle", NS):
        style_id = p_style.attrib.get(f"{{{NS['w']}}}val")
        if style_id:
            counts[style_id] = counts.get(style_id, 0) + 1
    return counts


def _detect_title(paragraphs: list[str], path: Path) -> str:
    for text in paragraphs[:20]:
        if (
            len(text) > 20
            and not re.match(r"^(удк|уdc|udc)\b", text, re.IGNORECASE)
            and not text.lower().startswith("doi:")
            and "doi.org" not in text.lower()
            and not _looks_like_author_line(text)
        ):
            return text[:180]
    return path.stem[:180]


def _count_references(paragraphs: list[str]) -> int:
    in_refs = False
    count = 0
    for paragraph in paragraphs:
        if _looks_like_references_title(paragraph):
            in_refs = True
            continue
        if in_refs and (re.match(r"^\s*\d+[\.\)]\s+", paragraph) or len(paragraph) > 30):
            count += 1
    return count


def _safe_style(paragraph, style_name: str) -> None:
    try:
        paragraph.style = style_name
    except Exception:
        return


def _looks_like_author_line(text: str) -> bool:
    return len(text) < 180 and bool(re.search(r"\b[A-ZА-ЯІЇЄҐ][a-zа-яіїєґ']+\s+[A-ZА-ЯІЇЄҐ]\.", text))


def _looks_like_title(text: str) -> bool:
    return len(text) > 35 and text.upper() == text and not _looks_like_references_title(text)


def _looks_like_references_title(text: str) -> bool:
    return text.strip().lower() in {"список використаних джерел", "література", "references", "reference"}


def _looks_like_figure_caption(text: str) -> bool:
    return bool(re.match(r"^(рис\.?|figure)\s*\d+", text.strip(), re.IGNORECASE))


def _looks_like_table_caption(text: str) -> bool:
    return bool(re.match(r"^(табл\.?|таблиця|table)\s*\d+", text.strip(), re.IGNORECASE))


def _normalized_contains(final_text: str, source_text: str) -> bool:
    if source_text in final_text:
        return True
    significant = [chunk for chunk in source_text.split(" ") if len(chunk) > 8]
    if not significant:
        return False
    found = sum(1 for chunk in significant if chunk in final_text)
    return found / len(significant) >= 0.97


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _repair_mojibake(text: str) -> str:
    if "Р" not in text and "С" not in text:
        return text
    try:
        repaired = text.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return text
    if repaired.count("�") > text.count("�"):
        return text
    return repaired


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_service_file(path: Path) -> bool:
    return path.name.startswith("~$") or path.name.startswith("._")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
