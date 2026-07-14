---
name: naukainfo-legacy-doc-image-recovery
description: Recovers images omitted by legacy binary DOC conversion and blocks release until recovered media are visually matched and reinserted in source order.
version: "2.9.0"
---
# Legacy DOC recovery

A DOC→DOCX conversion is not proof that all author media survived. For binary `.doc` sources, compare source rendering, converted media parts, and OLE streams (`WordDocument`, `Data`, `0Table/1Table`).

If source rendering shows an image missing from converted DOCX:
1. Preserve the source and all prior releases unchanged.
2. Run `scripts/recover_legacy_doc_images.py` into a separate recovery folder.
3. Match recovered images visually to the source page and caption.
4. Reinsert the exact recovered bytes in original order as a stable inline object unless the original anchor can be safely preserved.
5. Apply `РИС` to the object paragraph and the caption contract to its caption.
6. Compare SHA-256, relationships, page bounds, order, and final render.

Never invent, redraw, crop, replace, or omit author media. Ambiguity is `MEDIA_FIDELITY_BLOCKED`.
