---
name: naukainfo-etalon-slot-insertion
description: Inserts one or more validated article copies into the structural content slot of ETALON-JOURNAL.docx: after the TABLE OF CONTENTS page break and immediately before the section-break paragraph that begins the protected tail page. Preserves the template shell, page numbering, media, article objects and tail page. Use for diagnostic article-in-template tests and journal assembly.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; DOCX composition support required.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Preconditions

- Match is validated by author name and article title.
- ETALON and raw article hashes are captured.
- Work is performed on copies only.
- Requested output mode is explicit: original-authentic or normalized 11 pt/single.

# Structural slot rule

Do not use hard-coded paragraph numbers.

1. Find the paragraph whose visible text is `TABLE OF CONTENTS`.
2. Continue forward to the page-break paragraph that closes the contents page.
3. Find the next paragraph that owns `w:sectPr`; this section break begins the protected tail page.
4. Insert article body elements immediately before that section-break paragraph.

This location keeps the contents page in front, starts inserted articles on the existing next page, and leaves the protected tail page after all inserted content.

# Composition requirements

- Never overwrite `ETALON-JOURNAL.docx`.
- Merge styles, numbering, relationships and media; do not copy only plain text.
- Preserve tables, merged cells, figures, captions, drawings, hyperlinks, lists and authored page breaks.
- Remove the article-level terminal section properties when they would replace master page setup.
- Each additional article starts on a new page.
- Preserve the master document-level section settings and protected tail section.

# Two supported outputs

## Original-authentic

Insert the untouched validated article copy and preserve all authored typography.

## Minimal normalization

First apply `naukainfo-minimal-normalization`, then insert the resulting copy. Default typography is 11 pt and single line spacing while preserving emphasis and objects.

# Mandatory validation

After composition:

1. Confirm ETALON and raw hashes are unchanged.
2. Confirm all article paragraphs occur in the output in source order.
3. Confirm table and drawing counts equal template plus article counts.
4. Confirm temporary insertion markers are absent.
5. Render every page to PNG and inspect all pages.
6. Confirm article starts after TABLE OF CONTENTS and protected tail page remains last.

# Done when

Both structural and visual checks pass and the output is explicitly labeled diagnostic or production.
