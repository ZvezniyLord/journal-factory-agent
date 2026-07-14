---
name: naukainfo-media-object-fidelity-gate
description: Blocks journal assembly when any image, drawing, SmartArt, shape, textbox, nested image/table, formula, OLE object, caption, or source note from the article body is lost, reordered, detached from its caption, or rendered outside the page bounds.
version: "2.8.0"
---

# Non-negotiable gate

Article-body media is protected author content. A built journal is invalid if any article loses a drawing, image, SmartArt, grouped shape, textbox, nested table, caption, or source note.

# Root-cause lesson

A previous build lost **Figure 2** in the Magdysiuk article. Paragraph text checks passed, but the DrawingML relationship/media part was not carried through. This proves that text checks are insufficient.

# Required audit per article

Before normalization and after journal assembly, compute and compare:

- drawing/inline/anchor counts;
- `a:blip` rIds and media targets;
- VML/object/OLE/embedded package counts;
- textboxes and `w:txbxContent` blocks;
- tables nested inside textboxes/shapes;
- nearby captions: `Рис.`, `Fig.`, `Figure`, `Мал.`, `Таблиця`, `Table`;
- order signatures: text paragraph → object → caption/source note.

# Fix strategy

- Copy missing media bytes and relationships from the article source, not from a previous generated journal.
- Preserve object order and anchors where possible.
- If a missing object cannot be reattached automatically, stop with `MEDIA_FIDELITY_BLOCKED` and return the article name, source paragraph signature, and missing rId/media target.
- After repair, render and visually inspect the page containing every recovered object.

# Stop conditions

- Source has N drawings/media objects and final has fewer.
- A caption exists without its object, or object exists without its source caption.
- Object is clipped, outside margins, or extends beyond the printable page.
- Shape/textbox content is not inspected recursively.

## v2.9 extension

Counts alone are not proof. Compare relationship targets, SHA-256 hashes, dimensions, order signatures, and source-page visual evidence. For binary `.doc`, invoke the legacy recovery skill when conversion omits media.

## v3.0 source-to-final object completeness

Audit every article independently, not only the aggregate journal. A source article with two chart/figure objects must still have both in the final article region. Conference 136 regression fixtures include Magdysiuk Figure 2 and Todorova Figure 2; either missing object is a hard release blocker. Verify object order, relationship target, media hash, caption adjacency, and rendered presence.
