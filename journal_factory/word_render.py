from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import subprocess
import sys

from pypdf import PdfReader

from .archive_workspace import sha256_file


def render_docx_to_pdf(docx_path: Path, pdf_path: Path, report_path: Path) -> dict[str, Any]:
    docx_path = docx_path.resolve()
    pdf_path = pdf_path.resolve()
    report_path = report_path.resolve()
    blockers: list[str] = []
    if sys.platform != "win32":
        blockers.append("word_com_requires_windows")
        return _write_report(report_path, _blocked_report(docx_path, pdf_path, blockers))
    if not docx_path.is_file():
        blockers.append("input_docx_missing")
        return _write_report(report_path, _blocked_report(docx_path, pdf_path, blockers))

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    host_report = report_path.with_name(f"{report_path.stem}.word.json")
    script = r"""
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
$document = $null
try {
  $document = $word.Documents.Open($env:JF_RENDER_DOCX)
  $fieldCount = $document.Fields.Count
  $tocCount = $document.TablesOfContents.Count
  foreach ($toc in $document.TablesOfContents) { [void]$toc.Update() }
  foreach ($section in $document.Sections) {
    foreach ($header in $section.Headers) {
      if ($header.Exists -and $header.Range.Fields.Count -gt 0) { [void]$header.Range.Fields.Update() }
    }
    foreach ($footer in $section.Footers) {
      if ($footer.Exists -and $footer.Range.Fields.Count -gt 0) { [void]$footer.Range.Fields.Update() }
    }
  }
  if ($tocCount -gt 0) { $document.Save() }
  $document.ExportAsFixedFormat($env:JF_RENDER_PDF, 17)
  $pageCount = $document.ComputeStatistics(2)
  [pscustomobject]@{
    word_version = $word.Version
    field_count = $fieldCount
    toc_count = $tocCount
    page_count = $pageCount
  } | ConvertTo-Json | Set-Content -Encoding UTF8 $env:JF_RENDER_HOST_REPORT
} finally {
  if ($null -ne $document) { $document.Close(0) }
  $word.Quit()
}
"""
    env = dict(os.environ)
    env["JF_RENDER_DOCX"] = str(docx_path)
    env["JF_RENDER_PDF"] = str(pdf_path)
    env["JF_RENDER_HOST_REPORT"] = str(host_report)
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        blockers.append(f"word_render_exception:{type(exc).__name__}:{exc}")
        return _write_report(report_path, _blocked_report(docx_path, pdf_path, blockers))

    if completed.returncode != 0:
        error = completed.stderr.strip().replace("\n", " ")[:1000]
        blockers.append(f"word_render_exit:{completed.returncode}:{error}")
    if not pdf_path.is_file():
        blockers.append("rendered_pdf_missing")

    host: dict[str, Any] = {}
    if host_report.is_file():
        try:
            host = json.loads(host_report.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            blockers.append(f"word_host_report_invalid:{type(exc).__name__}:{exc}")
        host_report.unlink(missing_ok=True)

    pdf_pages = 0
    if pdf_path.is_file():
        try:
            pdf_pages = len(PdfReader(str(pdf_path)).pages)
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"pdf_validation_exception:{type(exc).__name__}:{exc}")
    if pdf_path.is_file() and pdf_pages <= 0:
        blockers.append("pdf_has_no_pages")
    word_pages = int(host.get("page_count") or 0)
    if word_pages and pdf_pages and word_pages != pdf_pages:
        blockers.append(f"page_count_mismatch:{word_pages}:{pdf_pages}")

    report = {
        "status": "PASS" if not blockers else "BLOCKED",
        "renderer": "Microsoft Word COM",
        "word_version": str(host.get("word_version") or ""),
        "input_docx": str(docx_path),
        "input_docx_sha256": sha256_file(docx_path),
        "output_pdf": str(pdf_path),
        "output_pdf_sha256": sha256_file(pdf_path) if pdf_path.is_file() else "",
        "word_field_count": int(host.get("field_count") or 0),
        "word_toc_count": int(host.get("toc_count") or 0),
        "word_page_count": word_pages,
        "pdf_page_count": pdf_pages,
        "blockers": blockers,
    }
    return _write_report(report_path, report)


def _blocked_report(docx_path: Path, pdf_path: Path, blockers: list[str]) -> dict[str, Any]:
    return {
        "status": "BLOCKED",
        "renderer": "Microsoft Word COM",
        "word_version": "",
        "input_docx": str(docx_path),
        "input_docx_sha256": sha256_file(docx_path) if docx_path.is_file() else "",
        "output_pdf": str(pdf_path),
        "output_pdf_sha256": "",
        "word_field_count": 0,
        "word_toc_count": 0,
        "word_page_count": 0,
        "pdf_page_count": 0,
        "blockers": blockers,
    }


def _write_report(report_path: Path, report: dict[str, Any]) -> dict[str, Any]:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
