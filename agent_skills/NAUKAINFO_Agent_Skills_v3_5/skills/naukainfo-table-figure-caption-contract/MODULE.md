---
name: naukainfo-table-figure-caption-contract
description: Applies and audits the verified NAUKAINFO publication contract for table numbers, table titles, table-cell text, source notes, drawing paragraphs and figure captions after an article is inserted into ETALON. Use before pagination and visual QA.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; NAUKAINFO ETALON styles; Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

Prevent author formatting, copied direct properties, or ETALON style inheritance from producing inconsistent table/figure captions or first-line indents.

# Verified contract

## Tables

1. Table number is a separate paragraph above the title: `Таблиця N` / `Table N`.
2. The number is right aligned, bold, 11 pt, single, first-line indent 0, spacing before/after 0, and kept with the next paragraph.
3. The table title is the next non-empty paragraph and must use the actual ETALON `РисПід` style (`styleId af6`), centered, bold, 11 pt, single, first-line indent 0, spacing before/after 0, and kept with the table. `Normal` plus direct formatting is not accepted.
4. Every paragraph inside every table cell uses actual ETALON style `TABLETEXT`.
5. Preserve author cell alignment, bold/italic emphasis, merged cells, widths, row heights, vertical alignment and repeating headers.
6. No table-cell paragraph may inherit a positive first-line indent from `Normal`.
7. A source/note below the table is 11 pt, single, first-line indent 0; preserve author italic and alignment unless the project explicitly normalizes it.

## Figures / SmartArt / shapes

1. The paragraph containing the object uses actual style `РИС`, centered, first-line indent 0.
2. The caption is below the object and uses actual style `РисПід`, centered, 11 pt, single, first-line indent 0.
3. Caption form is `Рис. N. Назва` unless the source language requires `Figure N. ...`.
4. Source/note below the caption has first-line indent 0 and preserves author emphasis.
5. Preserve anchors, wrap, size, DrawingML/SmartArt relationships and editability.

# Procedure

1. Detect table-number, table-title, figure-object, figure-caption and source-note paragraphs semantically.
2. Apply actual ETALON styles where verified. The table number uses controlled direct formatting; the table title uses actual `РисПід` (`af6`).
3. Remove only conflicting direct paragraph indents/spacing; do not flatten content or run emphasis.
4. Reopen the saved DOCX and audit actual style IDs and effective indentation.
5. Render every page containing a table or figure at 100% and inspect captions, splits, clipping and object geometry.

Use `scripts/finalize_business_semantics.py` as the authoritative finalizer. `normalize_captions_references.py` remains only as a lower-level compatibility utility and is not the acceptance gate.

# Stop conditions

Stop for operator review if a caption boundary is ambiguous, a table title is not adjacent to its table, a figure caption is embedded in a text box, or a layout change causes a table split rougher than the project 60/40 rule.

# Done when

All table/figure semantic roles follow this contract, objects and cell structure are unchanged, and rendered pages match publication expectations.
