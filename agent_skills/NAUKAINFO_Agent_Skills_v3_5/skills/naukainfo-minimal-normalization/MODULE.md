---
name: naukainfo-minimal-normalization
description: Normalizes article copies with minimal visual change: 11 pt, single spacing, table paragraphs without first-line indent, and shape/textbox text at 11 pt while preserving body order, emphasis, objects, anchors, numbering, and author intent. Use only on workspace copies after a validated plan.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.2.0"
---

# Safety first

1. Call `snapshot_inputs` before write operations.
2. Work only on a copied article in workspace.
3. Use the existing project normalizer through `prepare_conference` or the project’s specific normalizer tool; do not reimplement DOCX editing in the skill.

## Allowed default changes

- body font size 11 pt;
- single line spacing;
- table cell text 11 pt and single;
- no first-line indent in table cells; verify the effective value through style inheritance and invoke `naukainfo-table-format-fidelity` after ETALON insertion;
- shape/textbox text 11 pt and single;
- minimal table/image/caption alignment repair.

## Preserve

- paragraph order and content;
- bold/italic/underline where authored;
- structural, template, section and article-start page breaks;
- author-inserted internal page breaks by default, except pagination-helper candidates explicitly evaluated by `naukainfo-pagination-break-reflow`;
- list and reference numbering unless a specific repair is approved;
- table merges, widths and row properties unless overflow repair is needed;
- inline/floating image geometry and anchors;
- formulas, drawings, pict, embeddings and OLE.

## Validation loop

After normalization compare source vs copy:
- text tokens excluding allowed service cleanup;
- table/image/formula/shape/OLE counts;
- reference numbering;
- page/object geometry when Word rendering is available.

After 11 pt / single normalization, invoke `naukainfo-pagination-break-reflow` for manual breaks near tables because font reduction may make an old pagination helper obsolete.

After insertion into ETALON, invoke `naukainfo-semantic-style-routing` and `naukainfo-table-format-fidelity`; a target `Normal` style may add an effective indent even when the copied paragraph has no direct indent property.

Stop and report on unexplained loss.


If editable figures are detected, invoke `naukainfo-shape-object-fidelity` before and after insertion.
