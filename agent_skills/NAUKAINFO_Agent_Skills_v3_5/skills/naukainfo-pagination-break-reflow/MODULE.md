---
name: naukainfo-pagination-break-reflow
description: Re-evaluates author-inserted manual page breaks after font-size and spacing normalization, especially around tables. Removes only obsolete pagination-helper breaks after rendered comparison confirms acceptable publication aesthetics and table continuity; preserves structural and article-start breaks.
license: Proprietary project skill
compatibility: Windows 11; Microsoft Word rendering recommended; Python 3.11+; NAUKAINFO Journal Builder project.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

Authors may insert a manual page break while preparing an article at 14 pt so that a table starts or continues cleanly. After normalization to 11 pt and single spacing, that break may create an unnecessary blank area or force a table onto a new page even though the preceding page now has enough space. Re-evaluate such breaks only after normalization and only on a workspace copy.

## Hard boundaries

Never remove:

- the page break that starts a new article;
- ETALON/template structural breaks;
- section breaks or paragraph-level `w:sectPr`;
- breaks required to protect cover, contents, service, or tail pages;
- a break whose purpose cannot be identified confidently.

Treat only author-inserted pagination-helper page breaks near tables, captions, or table-introducing paragraphs as candidates.

## Candidate detection

Inspect explicit `w:br w:type="page"`, `pageBreakBefore`, and equivalent Word pagination properties:

1. immediately before a table or its caption;
2. between consecutive parts of one logical table;
3. in the short paragraph sequence after a table-introducing sentence;
4. where the source at a larger font size shows a table-preservation intent.

Record the exact paragraph/table position and the evidence for classifying it as a candidate.

## Required comparison

Create two temporary copies after 11 pt / single normalization:

- **A — preserved break**;
- **B — candidate break removed**.

Render both with Word-compatible pagination. Do not decide from OOXML text flow alone when rendering is available.

## Removal criteria

Remove the candidate only when all conditions are satisfied:

1. no text, table row, image, formula, caption, footnote, or object is lost, clipped, overlapped, or reordered;
2. the result looks suitable for a published proceedings volume and does not create an excessive blank zone;
3. the table either:
   - fits wholly on one page; or
   - splits across pages in a balanced way no rougher than approximately **60/40** by table volume;
4. the caption/number and table header are not orphaned from the table body;
5. repeated header rows, merged cells, row non-splitting settings, and notes under the table remain correct;
6. the following page does not begin with only a tiny residual fragment of the table.

A 60/40 threshold means the smaller page fragment should represent about 40% or more of the table and the larger fragment about 60% or less. A more balanced 50/50 split is acceptable. A 70/30, 80/20, single-row, or similarly abrupt split is not acceptable by default.

## Measuring the split

Preferred metric: rendered vertical height occupied by the table on each page.

Fallback when reliable rendered geometry is unavailable:

- use weighted row height rather than raw row count;
- include merged-row span and fixed row heights;
- exclude caption and source note from table-volume percentage, but evaluate them separately for orphaning.

If the metric is uncertain or close to the threshold, preserve the break and mark `needs_operator_review`.

## Decision outcomes

- `remove_obsolete_break`: all criteria pass;
- `preserve_break`: removal damages layout or creates an unbalanced table split;
- `needs_operator_review`: intent or rendered result is ambiguous.

## Audit trail

For every evaluated break record:

- article ID, author, and title;
- source file and normalized copy;
- OOXML location/type of break;
- reason the break was considered author-inserted;
- table identifier and page numbers in variants A and B;
- split ratio or “fits whole page” result;
- before/after screenshots or rendered PDF pages;
- final decision and confidence.

## Done when

The chosen copy passes text/object integrity checks, pagination rendering, and visual regression review, with every removed break explained in the audit report.
