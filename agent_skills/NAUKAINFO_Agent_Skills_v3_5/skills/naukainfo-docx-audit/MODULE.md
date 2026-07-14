---
name: naukainfo-docx-audit
description: Runs structural, text, object, Excel reconciliation, UDC/DOI, empty paragraph, section order, references numbering, table, shape/textbox, and source immutability checks on a built journal. Use after every diagnostic or full build and before finalization.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.1.0"
---

# Audit order

1. Verify source and ETALON hashes unchanged.
2. Excel vs journal reconciliation: all expected articles, no extras/duplicates.
3. Text integrity: no unexplained content loss.
4. Object integrity: tables, images, formulas, shapes/textboxes, OLE, media/embeddings.
5. Front matter: DOI/UDC/authors/title ordering and missing fields.
6. Sections/order/page starts.
7. Tables: exact source↔target text/structure, effective first-line indent through style inheritance, alignment, runs, font/spacing, cell/row geometry and rendered fit. Route mismatches to `naukainfo-table-format-fidelity`.
8. References: each article restarts at 1; no lost numbering.
9. Shape/textbox font and geometry.
10. Produce operator actions separated into critical, high, medium and low.

## Severity

Critical:
- missing article;
- text/object loss;
- corrupted/open-failing DOCX;
- ETALON/raw modification;
- broken article order;
- missing title/author that prevents identification.

Warning/manual review:
- generated UDC;
- ambiguous header line;
- table geometry not safely measurable;
- caption style variation;
- low-priority blank page from trailing empty paragraphs.

Never mark final based only on the agent’s subjective visual impression.
