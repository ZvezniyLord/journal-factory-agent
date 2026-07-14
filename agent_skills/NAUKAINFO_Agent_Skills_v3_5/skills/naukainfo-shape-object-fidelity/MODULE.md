---
name: naukainfo-shape-object-fidelity
description: Preserves SmartArt, grouped shapes, text boxes, DrawingML/VML fallback content, embedded text, relationship parts, extents, anchors, and visual layout when an article is normalized and inserted into ETALON. Use whenever a DOCX contains editable figures with text rather than only raster images.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; lxml; python-docx; Microsoft Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

Editable figures with text are not ordinary images. SmartArt and grouped Word shapes can depend on multiple OOXML parts and relationships. A naive body copy may preserve the visible placeholder but lose the diagram drawing part, text, geometry or fallback representation.

# Detection

Before normalization or insertion, inspect the DOCX package for:

- `dgm:relIds` and `word/diagrams/data*.xml`;
- `word/diagrams/drawing*.xml` and diagram drawing relationships;
- `w:txbxContent` in DrawingML or VML shapes;
- grouped shapes, anchors/inlines and extents;
- fallback `mc:AlternateContent` branches;
- charts, OLE and embedded objects near the same paragraph.

# Source-of-truth checks

For every SmartArt/shape object compare source and target:

- ordered text signature inside shapes;
- object count and type;
- data-model and drawing relationship validity;
- drawing part bytes/XML where exact preservation is expected;
- extent (`cx`, `cy`), anchor/inline mode and position;
- text-box paragraph/run order and text;
- font size after the allowed 11 pt normalization;
- rendered visual arrangement, connectors, borders and text wrapping.

# Safe transfer procedure

1. Copy the source article and normalize ordinary paragraphs/tables.
2. Patch text inside `w:txbxContent` and DrawingML/SmartArt runs to 11 pt without rasterizing the object.
3. Insert article body into a copy of ETALON.
4. Audit SmartArt relationships by exact text signature.
5. If the target data model exists but its `diagramDrawing` relationship/part is missing, copy the verified source drawing part, add a new relationship and content-type override, and patch the target `dataModelExt` relationship id.
6. Refuse automatic repair when a drawing part has dependent relationships that are not copied deterministically.
7. Reopen, audit and render all pages.

Use:

- `scripts/normalize_11_with_shapes.py` for 11 pt normalization inside text boxes/SmartArt;
- `scripts/shape_object_fidelity.py` for relationship and content fidelity auditing/repair.

# Verified case

The skill was validated on article `136/Заявки/27 Гнисюк/Гнисюк_тези.docx`, which contains a SmartArt-style motivation diagram with four text blocks. The source and ETALON copy retained the exact text signature, extent and drawing XML after repair and rendered correctly.

# Stop conditions

- missing or ambiguous source object;
- unmatched text signatures;
- dependent drawing relationships;
- lost text-box content;
- geometry drift, clipping, overlap or connector loss;
- any rasterization not explicitly approved.

# Done when

All editable figure objects remain editable, their text and relationships match the source, 11 pt normalization is applied where authorized, and every rendered page passes visual inspection.
