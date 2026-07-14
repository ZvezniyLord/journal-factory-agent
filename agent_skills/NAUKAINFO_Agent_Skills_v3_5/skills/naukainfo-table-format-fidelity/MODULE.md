---
name: naukainfo-table-format-fidelity
description: Preserves table text placement when articles are normalized or inserted into ETALON. Compares source and target table paragraphs using effective style inheritance, removes unintended first-line indents introduced by the template, and verifies alignment, spacing, runs, cells, rows, merges, widths, and rendered pagination.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; Microsoft Word or LibreOffice rendering; NAUKAINFO Journal Builder project.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

A copied table may look different even when its paragraph XML has no direct indent. The target template can define a non-zero first-line indent in `Normal`, and table paragraphs that use `Normal` silently inherit it. Therefore direct-property checks alone are insufficient.

Use this skill after normalization and after insertion into `ETALON-JOURNAL.docx`, before final visual approval.

# Source of truth

1. The original article is the primary reference for table text placement.
2. The project default is no first-line indent inside table cells.
3. A deliberate non-zero source indent is preserved only when clearly authored and operator-approved.
4. Never repair the issue by globally changing the ETALON `Normal` style, because that would alter body paragraphs and service pages.

# Required checks for every table

Compare source and target by table index and cell coordinates:

- table count, row count, column count and merged-cell structure;
- exact cell text and paragraph count;
- effective first-line indent, including paragraph style and base-style inheritance;
- left/right indent, alignment, line spacing and before/after spacing;
- bold, italic, underline, font size and run order;
- cell vertical alignment and margins;
- table width, column widths, row height, row splitting and repeating headers;
- captions, notes/sources and page placement;
- rendered table split and absence of clipping or overlap.

# Effective-format rule

Do not treat `paragraph_format.first_line_indent is None` as proof that there is no indent.

Resolve the effective value in this order:

1. direct paragraph property;
2. paragraph style;
3. base-style chain;
4. document default.

When the source effective first-line indent is zero and the target inherits a non-zero indent, add an explicit direct zero override (`w:firstLine="0"`) to the target table paragraph.

# Safe repair procedure

1. Work on a workspace copy.
2. Run `scripts/table_format_fidelity.py` with source, target and output paths.
3. Refuse automatic repair if table count or structure differs materially.
4. Apply only the missing direct indent override; do not rewrite text or reconstruct tables.
5. Re-open the saved DOCX and repeat the structural comparison.
6. Require zero unexplained table-paragraph differences.
7. Render the entire document and inspect every page, with special attention to all pages containing tables and captions.
8. If font reduction changed page breaks, route separately to `naukainfo-pagination-break-reflow`.

# Audit trail

Record:

- source and target filenames;
- table/row/cell/paragraph coordinates;
- source and target effective indent with inheritance source;
- exact repair applied;
- remaining differences after save/re-open;
- table page numbers in the rendered document;
- final result: `pass`, `needs_operator_review`, or `fail`.

# Stop conditions

Stop and request operator review when:

- source and target table structure differ;
- merged cells cannot be mapped reliably;
- cell text differs;
- an indentation change appears intentional in the source;
- the repair creates clipping, a poor split, or a caption/table orphan;
- any other table typography or placement difference remains unexplained.

# Done when

All table text, paragraph/run formatting and placement match the source except explicitly approved normalization, effective first-line indent is correct, and the rendered document passes visual review.
