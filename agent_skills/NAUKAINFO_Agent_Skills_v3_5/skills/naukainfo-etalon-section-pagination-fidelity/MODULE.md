---
name: naukainfo-etalon-section-pagination-fidelity
description: Preserves the ETALON section-break graph, footer relationships, and internal page-number start so journal pagination remains identical to the template after assembly.
license: Proprietary project skill
compatibility: Word DOCX/OOXML; NAUKAINFO ETALON; Дирежор project only.
metadata:
  author: naukainfo
  version: "3.0.0"
---

# Purpose

The ETALON contains a deliberate three-section layout. The middle section carries the running footer/page field and `w:pgNumType w:start="1"`; the protected final service page is a separate section. Losing or flattening these `sectPr` nodes makes page numbers disappear or restart incorrectly.

# Contract

1. Work on a copy of ETALON and preserve its complete ordered `w:sectPr` sequence.
2. Preserve section-break positions, `footerReference`/`headerReference` relationships, `w:pgNumType`, page size, margins, columns, and title-page flags.
3. Insert the article body only into the designated middle content section; do not rebuild the document body from plain XML fragments that discard section properties.
4. Preserve the required template page break between the copyright/front matter and `TABLE OF CONTENTS`.
5. Preserve the protected final service-page section.
6. After assembly, assert the expected section count and the exact numbered section signature from ETALON.
7. Render the whole journal and verify visible internal page numbers on TOC/article pages.

# Fail closed

Stop with `ETALON_SECTION_PAGINATION_BLOCKED` when section count, footer relationships, `pgNumType`, or visible page numbers differ from ETALON. Never repair missing numbers by adding ad-hoc typed numerals.

# Worked

Preserving all three ETALON sections, including the middle `start=1` page-number section and its footer relationship.

# Removed from active logic

Replacing the article area while dropping body-level `sectPr`, or assuming a visually similar single-section document is acceptable.
