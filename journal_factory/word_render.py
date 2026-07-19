from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import subprocess
import sys

from pypdf import PdfReader

from .archive_workspace import sha256_file
from .official_toc import load_official_toc
from .publication_audit import (
    audit_pdf_pages,
    build_toc_pagination_report,
    expected_first_article_pages,
)


def render_docx_to_pdf(
    docx_path: Path,
    pdf_path: Path,
    report_path: Path,
    expected_article_count: int | None = None,
    expected_first_article_page: int | None = None,
    official_toc_path: Path | None = None,
) -> dict[str, Any]:
    docx_path = docx_path.resolve()
    pdf_path = pdf_path.resolve()
    report_path = report_path.resolve()
    blockers: list[str] = []
    official_toc: dict[str, Any] | None = None
    if official_toc_path is not None:
        try:
            official_toc = load_official_toc(official_toc_path.resolve())
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"official_toc_invalid:{type(exc).__name__}:{exc}")
            return _write_report(report_path, _blocked_report(docx_path, pdf_path, blockers))
        expected_article_count = expected_article_count or len(official_toc["articles"])
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
  $listSeparator = (Get-Culture).TextInfo.ListSeparator
  $tocStyleMapping = "SECTION${listSeparator}1${listSeparator}Назва1${listSeparator}2"
  $manualToc = $false
  foreach ($toc in $document.TablesOfContents) {
    $tocField = $toc.Range.Fields.Item(1)
    if ($tocField.Locked) {
      $manualToc = $true
    } else {
      $tocField.Code.Text = " TOC \h \z \t `"${tocStyleMapping}`" "
    }
  }
  $measurements = @()
  $stableCount = 0
  $previousKey = ''
  for ($iteration = 1; $iteration -le 6; $iteration++) {
    [void]$document.Repaginate()
    foreach ($field in $document.Fields) {
      $fieldCode = [string]$field.Code.Text
      if ($manualToc) {
        if ($fieldCode -match '(?i)^\s*(?:PAGEREF|PAGE|NUMPAGES)\b') {
          [void]$field.Update()
        }
      } elseif ($field.Type -eq 26) {
        [void]$field.Update()
      }
    }
    if (-not $manualToc) {
      foreach ($toc in $document.TablesOfContents) { [void]$toc.Update() }
    }
    foreach ($builtinStyle in @(-20, -21)) {
      try {
        $tocStyle = $document.Styles.Item($builtinStyle)
        $tocStyle.Font.Name = 'Times New Roman'
        $tocStyle.Font.Size = $(if ($manualToc) { 14 } else { 8 })
        $tocStyle.ParagraphFormat.SpaceBefore = 0
        $tocStyle.ParagraphFormat.SpaceAfter = 0
        $tocStyle.ParagraphFormat.LineSpacingRule = 0
      } catch {
        # Word creates built-in TOC styles lazily; the next pass retries.
      }
    }
    [void]$document.Repaginate()
    $pageCount = $document.ComputeStatistics(2)
    $tocCount = $document.TablesOfContents.Count
    $tocTextLength = 0
    $tocStartPage = 0
    $tocEndPage = 0
    if ($tocCount -gt 0) {
      $tocRange = $document.TablesOfContents.Item(1).Range
      $tocTextLength = $tocRange.Text.Length
      $tocStart = $document.Range($tocRange.Start, $tocRange.Start)
      $tocEnd = $document.Range($tocRange.End - 1, $tocRange.End - 1)
      $tocStartPage = $tocStart.Information(3)
      $tocEndPage = $tocEnd.Information(3)
    }
    $key = "${pageCount}|${tocCount}|${tocTextLength}|${tocStartPage}|${tocEndPage}"
    if ($key -eq $previousKey) { $stableCount++ } else { $stableCount = 1 }
    $previousKey = $key
    $measurements += [pscustomobject]@{
      iteration = $iteration
      page_count = $pageCount
      toc_count = $tocCount
      toc_text_length = $tocTextLength
      toc_start_page = $tocStartPage
      toc_end_page = $tocEndPage
      stable_streak = $stableCount
    }
    if ($stableCount -ge 2) { break }
  }
  $document.Save()
  $tocStyleNames = @{}
  foreach ($level in @(1, 2)) {
    try { $tocStyleNames[[string]$level] = [string]$document.Styles.Item(-19 - $level).NameLocal } catch {}
  }
  $tocEntries = @()
  foreach ($toc in $document.TablesOfContents) {
    foreach ($paragraph in $toc.Range.Paragraphs) {
      $styleName = ''
      try { $styleName = [string]$paragraph.Style.NameLocal } catch { $styleName = [string]$paragraph.Style }
      $entryText = ([string]$paragraph.Range.Text).Trim([char]13, [char]7, [char]32)
      $level = 0
      foreach ($candidateLevel in @(1, 2)) {
        if ($tocStyleNames[[string]$candidateLevel] -eq $styleName) { $level = $candidateLevel }
      }
      if ($level -eq 0 -and $styleName -match '(?i)(?:toc|зміст)\s*(\d+)') { $level = [int]$Matches[1] }
      if ($manualToc -and $level -eq 0) {
        $level = $(if ($entryText -match '^\d{1,3}\.\s+') { 2 } else { 1 })
      }
      $pageNumber = 0
      if ($entryText -match "`t(\d+)") { $pageNumber = [int]$Matches[1] }
      if ($entryText) {
        $tocEntries += [pscustomobject]@{
          level = $level
          style = $styleName
          text = $entryText
          page_number = $pageNumber
        }
      }
    }
  }
  $articleBookmarks = @()
  foreach ($bookmark in $document.Bookmarks) {
    if ($bookmark.Name -like 'JF_ARTICLE_*_START') {
      $bookmarkStart = $document.Range($bookmark.Start, $bookmark.Start)
      $articleBookmarks += [pscustomobject]@{
        name = [string]$bookmark.Name
        printed_page = [int]$bookmarkStart.Information(1)
        physical_page = [int]$bookmarkStart.Information(3)
      }
    }
  }
  $specialThanksPage = 0
  if ($document.Bookmarks.Exists('JF_SPECIAL_THANKS')) {
    $specialThanksRange = $document.Bookmarks.Item('JF_SPECIAL_THANKS').Range
    $specialThanksPage = [int]$specialThanksRange.Information(3)
  }
  $document.ExportAsFixedFormat($env:JF_RENDER_PDF, 17)
  $pageCount = $document.ComputeStatistics(2)
  [pscustomobject]@{
    word_version = $word.Version
    field_count = $document.Fields.Count
    toc_count = $document.TablesOfContents.Count
    manual_toc = $manualToc
    page_count = $pageCount
    stable_measurements = $measurements
    stable_measurements_achieved = $stableCount
    toc_entries = $tocEntries
    toc_style_names = $tocStyleNames
    article_bookmarks = $articleBookmarks
    special_thanks_physical_page = $specialThanksPage
  } | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $env:JF_RENDER_HOST_REPORT
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
            timeout=600,
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

    toc_count = int(host.get("toc_count") or 0)
    stable_achieved = int(host.get("stable_measurements_achieved") or 0)
    toc_entries = host.get("toc_entries") or []
    if isinstance(toc_entries, dict):
        toc_entries = [toc_entries]
    article_bookmarks = host.get("article_bookmarks") or []
    if isinstance(article_bookmarks, dict):
        article_bookmarks = [article_bookmarks]
    level_two_entries = [item for item in toc_entries if int(item.get("level") or 0) == 2]
    article_bookmarks = sorted(article_bookmarks, key=lambda item: str(item.get("name") or ""))
    if toc_count == 0:
        blockers.append("word_toc_missing")
    if stable_achieved < 2:
        blockers.append(f"word_layout_not_stable:{stable_achieved}:required=2")
    if expected_article_count is not None:
        if len(level_two_entries) != expected_article_count:
            blockers.append(
                f"toc_article_entry_count:{len(level_two_entries)}:expected={expected_article_count}"
            )
        if len(article_bookmarks) != expected_article_count:
            blockers.append(
                f"article_bookmark_count:{len(article_bookmarks)}:expected={expected_article_count}"
            )
    if expected_first_article_page is not None and article_bookmarks:
        first_printed = int(article_bookmarks[0].get("printed_page") or 0)
        first_physical = int(article_bookmarks[0].get("physical_page") or 0)
        expected_physical, expected_printed = expected_first_article_pages(
            expected_first_article_page,
            official_toc,
        )
        if first_printed != expected_printed or first_physical != expected_physical:
            blockers.append(
                f"first_article_page:{first_physical}:{first_printed}:"
                f"expected={expected_physical}:{expected_printed}"
            )
    page_numbering = (official_toc or {}).get("page_numbering")
    official_articles = (official_toc or {}).get("articles") or []
    special_thanks = (official_toc or {}).get("special_thanks") or {}
    special_thanks_page = int(host.get("special_thanks_physical_page") or 0)
    expected_special_thanks_page = int(special_thanks.get("physical_page") or 0)
    special_thanks_matched = (
        not special_thanks.get("present")
        or special_thanks_page == expected_special_thanks_page
    )
    if not special_thanks_matched:
        blockers.append(
            f"official_special_thanks_page:{special_thanks_page}:"
            f"expected={expected_special_thanks_page}"
        )
    page_mappings: list[dict[str, Any]] = []
    for index, bookmark in enumerate(article_bookmarks, start=1):
        physical = int(bookmark.get("physical_page") or 0)
        printed = int(bookmark.get("printed_page") or 0)
        official = official_articles[index - 1] if index <= len(official_articles) else None
        if official:
            expected_physical = int(official.get("physical_start_page") or 0)
            expected_printed = int(official.get("printed_start_page") or 0)
            matched = physical == expected_physical and printed == expected_printed
            if not matched:
                blockers.append(
                    f"official_article_start:{index}:{physical}:{printed}:"
                    f"expected={expected_physical}:{expected_printed}"
                )
            page_mappings.append(
                {
                    "ordinal": index,
                    "bookmark": bookmark.get("name"),
                    "official_title": official.get("title"),
                    "official_physical_page": expected_physical,
                    "generated_physical_page": physical,
                    "official_printed_page": expected_printed,
                    "generated_printed_page": printed,
                    "matched": matched,
                }
            )
        elif physical != printed:
            blockers.append(
                f"page_number_discontinuity:{bookmark.get('name')}:{physical}:{printed}"
            )
    if len(level_two_entries) == len(article_bookmarks):
        for entry, bookmark in zip(level_two_entries, article_bookmarks):
            toc_page = int(entry.get("page_number") or 0)
            printed = int(bookmark.get("printed_page") or 0)
            if toc_page != printed:
                blockers.append(
                    f"toc_page_mismatch:{bookmark.get('name')}:{toc_page}:{printed}"
                )

    expected_pdf_pages = int(
        (official_toc or {}).get("source", {}).get("physical_page_count") or pdf_pages
    )
    if official_toc and pdf_pages != expected_pdf_pages:
        blockers.append(f"official_pdf_page_count:{pdf_pages}:expected={expected_pdf_pages}")
    visual_report = audit_pdf_pages(
        pdf_path,
        expected_page_count=expected_pdf_pages,
        page_numbering=page_numbering,
    ) if pdf_path.is_file() else {
        "status": "BLOCKED",
        "blockers": ["pdf_missing"],
    }
    if visual_report.get("status") != "PASS":
        blockers.extend(f"visual_qa:{item}" for item in visual_report.get("blockers") or [])
    toc_pagination_path = report_path.with_name("toc_pagination_report.json")
    official_page_parity_path = report_path.with_name("official_page_parity.json")
    official_page_parity = {
        "schema_version": 1,
        "status": (
            "PASS"
            if official_toc
            and pdf_pages == expected_pdf_pages
            and len(page_mappings) == len(official_articles)
            and all(item["matched"] for item in page_mappings)
            and special_thanks_matched
            else ("NOT_REQUIRED" if not official_toc else "REVIEW")
        ),
        "official_pdf_sha256": (official_toc or {}).get("source", {}).get("sha256"),
        "official_physical_page_count": expected_pdf_pages if official_toc else None,
        "generated_physical_page_count": pdf_pages,
        "physical_to_printed_offset": (page_numbering or {}).get(
            "physical_to_printed_offset"
        ),
        "article_start_pages_match_official": bool(page_mappings)
        and len(page_mappings) == len(official_articles)
        and all(item["matched"] for item in page_mappings),
        "special_thanks": {
            "required": bool(special_thanks.get("present")),
            "official_physical_page": expected_special_thanks_page or None,
            "generated_physical_page": special_thanks_page or None,
            "matched": special_thanks_matched,
        },
        "mappings": page_mappings,
    }
    if official_toc:
        _write_report(official_page_parity_path, official_page_parity)
    report = {
        "status": "PASS" if not blockers else "BLOCKED",
        "renderer": "Microsoft Word COM",
        "word_version": str(host.get("word_version") or ""),
        "input_docx": str(docx_path),
        "input_docx_sha256": sha256_file(docx_path),
        "output_pdf": str(pdf_path),
        "output_pdf_sha256": sha256_file(pdf_path) if pdf_path.is_file() else "",
        "word_field_count": int(host.get("field_count") or 0),
        "word_toc_count": toc_count,
        "manual_official_toc": bool(host.get("manual_toc")),
        "word_page_count": word_pages,
        "pdf_page_count": pdf_pages,
        "stable_measurements_required": 2,
        "stable_measurements_achieved": stable_achieved,
        "stable_measurements": host.get("stable_measurements") or [],
        "toc_entries": toc_entries,
        "toc_style_names": host.get("toc_style_names") or {},
        "toc_level_counts": {
            str(level): sum(int(item.get("level") or 0) == level for item in toc_entries)
            for level in (1, 2)
        },
        "article_bookmarks": article_bookmarks,
        "official_page_parity": official_page_parity,
        "golden_publication_parity": {
            "required": bool(official_toc),
            "status": official_page_parity["status"],
        },
        "internal_consistency": {
            "toc_article_entry_count": len(level_two_entries),
            "article_bookmark_count": len(article_bookmarks),
            "toc_pages_match_generated_bookmarks": (
                len(level_two_entries) == len(article_bookmarks)
                and all(
                    int(entry.get("page_number") or 0)
                    == int(bookmark.get("printed_page") or 0)
                    for entry, bookmark in zip(level_two_entries, article_bookmarks)
                )
            ),
        },
        "visual_qa": visual_report,
        "toc_pagination_report": str(toc_pagination_path),
        "official_page_parity_report": (
            str(official_page_parity_path) if official_toc else None
        ),
        "blockers": blockers,
    }
    _write_report(report_path, report)
    build_toc_pagination_report(
        docx_path,
        report,
        visual_report,
        toc_pagination_path,
        expected_article_count=expected_article_count,
        expected_first_article_page=expected_first_article_page,
        official_toc=official_toc,
    )
    return report


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
        "stable_measurements_required": 2,
        "stable_measurements_achieved": 0,
        "stable_measurements": [],
        "toc_entries": [],
        "toc_style_names": {},
        "toc_level_counts": {"1": 0, "2": 0},
        "article_bookmarks": [],
        "blockers": blockers,
    }


def _write_report(report_path: Path, report: dict[str, Any]) -> dict[str, Any]:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
