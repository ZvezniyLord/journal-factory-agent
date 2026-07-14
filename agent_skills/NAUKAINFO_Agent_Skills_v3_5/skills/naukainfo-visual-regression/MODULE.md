---
name: naukainfo-visual-regression
description: Renders a built DOCX through Microsoft Word to PDF/page images and compares layout, blank pages, tables, images, shapes, captions, and page boundaries against source/reference artifacts. Use when visual authenticity matters or after any DOCX layout change.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.1.0"
---

# Requirements

Windows with Microsoft Word. Work on output copies only.

## Procedure

1. Call `render_docx_pdf` for the draft.
2. Record page count and detect blank pages.
3. Compare article boundary pages, pages containing tables, figures, shapes/textboxes and reference blocks. For tables, verify the first text line starts at the same horizontal position as in the source and that no style-inherited indent appears.
4. When a baseline exists, compare page images and produce a difference report.
5. Distinguish permitted differences (11 pt/single) from unintended movement, clipping, lost objects or numbering changes.

## Gotchas

- Object counts alone do not prove geometry preservation.
- A blank page from trailing empty paragraphs + an inter-article break is low/medium priority unless it affects pagination/TOC materially.
- Complex merged tables may not expose stable column widths through COM; require a visual checkpoint.
- Do not use OCR as the primary comparison when Word/PDF text extraction is available.
