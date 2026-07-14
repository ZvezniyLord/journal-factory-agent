---
name: naukainfo-shape-textbox-nested-table-contract
description: Recursively inspects DrawingML/VML shapes, textboxes, grouped objects, and nested tables so captions and table text inside shapes receive journal styles and do not overflow the page.
version: "2.8.0"
---

# Problem covered

Some authors insert what visually looks like a picture, but technically it is a shape/textbox/group containing a table and captions. In Matviienko-style articles, captions such as `РИС. 1. СХЕМА АРХІТЕКТУРИ МОДЕЛІ` may live inside `w:txbxContent`, and tables inside those shapes can inherit wrong spacing or first-line indent.

# Required recursion

Every shape audit must inspect:

- `w:drawing`, `wp:inline`, `wp:anchor`;
- `wps:txbx`, `v:textbox`, `w:txbxContent`;
- grouped shapes and nested paragraphs;
- `w:tbl` elements inside shapes/textboxes;
- captions and source notes inside shapes.

# Formatting rules inside shapes

- Figure captions inside shapes get `РисПід`/caption-equivalent formatting: 11 pt, single spacing, centered, no first-line indent.
- Table captions inside shapes follow the table-caption contract.
- Table cell paragraphs inside shapes get no first-line indent and single spacing.
- Shape/table width must be constrained to the printable area; no element may extend beyond page margins.

# Rendering gate

Render the page containing the nested shape at 100% zoom. The build fails if the shape/table overflows, clips, or loses text.

## v2.9 style routing

All drawing/object paragraphs, including containers with nested tables, receive `РИС`; all recognized captions inside or outside the container receive `РисПід`. Nested table paragraphs must have single spacing and zero first-line indent.

## v3.0 deep-container style assertion

The audit must assert both container and nested roles. The outer object paragraph receives `РИС`; every caption paragraph inside `w:txbxContent`/DrawingML/VML receives `РисПід` when it is a figure caption. Nested table labels/titles follow the canonical table-label/title split, and nested cell paragraphs receive single spacing with zero first-line indent. Compatibility-fallback duplicates in DrawingML/VML must be formatted consistently without deleting either branch.
