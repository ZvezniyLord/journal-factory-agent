---
name: naukainfo-toc-table-builder
description: Build NAUKAINFO TABLE OF CONTENTS as a real three-column Word table using canonical Tab_* styles, the PDF-proven row geometry, and post-render page numbers.
---

# NAUKAINFO TOC Table Builder

## Priority
High. The table of contents must be generated from the actual styled article body, not typed manually as loose paragraphs.

## Source of truth
Use the ETALON/Jurnal styles and compare the visual result with previously published NAUKAINFO PDFs. The verified PDF pattern is:

- `TABLE OF CONTENTS` title centered above the table;
- each section is a centered bold all-caps row;
- each article has a separate narrow number column, a wide author/title column, and a right page-number column;
- the author line is bold italic;
- the article title is on the next row in all caps;
- page number is aligned right on the author row.

## Canonical table geometry
1. Locate the placeholder/title paragraph `TABLE OF CONTENTS` in the ETALON/Jurnal template.
2. Delete all old TOC body content between `TABLE OF CONTENTS` and the first real article `SECTION` paragraph.
3. Insert one real Word table with exactly three physical columns.
4. Use fixed grid widths close to the PDF layout: narrow number column, wide content column, narrow right page column. Current working grid: `[600, 8300, 739]` twips.
5. Keep borders invisible/no borders.
6. Insert section rows as one merged row spanning all 3 columns. Do **not** repeat the section text separately in each cell.
7. For every article insert exactly two rows:
   - row A: column 1 = `N.`, column 2 = author(s), column 3 = verified page number;
   - row B: column 1 = blank, column 2 = article title, column 3 = blank.
8. Never put the title in the same row as the author. This was the v2.2 defect that made the content column too narrow and visually unlike the PDF.

## Required styles
Use the actual style IDs from the template, not guessed names:

| TOC role | Visible style name | OOXML styleId |
|---|---|---|
| section row | `Tab_SEC` | `TabSEC` |
| author cell | `Tab_PIP` | `TabPIP` |
| article title cell | `Tab_Taitl` | `TabTaitl` |
| article number cell | `Tab_Taitl` | `TabTaitl` |
| page number cell | `Tab_Taitl` + direct right alignment | `TabTaitl` |

## TOC record collection
1. Group records by the nearest preceding `SECTION` paragraph.
2. Collect author rows only from `AUTOR`.
3. Collect title only from `Назва1` / styleId `11` in the verified Word 2010 template.
4. Do not use `pip`, UDC, DOI, annotations, captions, references, table text or body paragraphs for TOC rows.
5. Deduplicate author names within one article and duplicate titles caused by front-matter reconstruction.

## Pagination workflow
1. Assemble the journal body first.
2. Render the document and determine actual internal article start pages.
3. Build or update the static TOC with final page numbers.
4. Render again and inspect the TOC page visually against a known PDF.
5. No `?` placeholders may remain.

## Failure modes that stop the build
- TOC is made of loose paragraphs instead of a 3-column table.
- Section text appears repeated in three cells instead of one merged section row.
- Article title appears in the same row as the author.
- A `pip` line enters the TOC.
- Any article has no `AUTOR` or no `Назва1`.
- Page numbers are stale after pagination changed.
- The TOC is visually narrower/wider than the PDF reference after render.

## What worked
- PDF-based reconstruction: section merged row + two article rows.
- Using `TabSEC`, `TabPIP`, `TabTaitl` style IDs directly from the template.
- Wide middle column so Ukrainian long titles wrap like the published PDF.

## What did not work and is removed from active logic
- v2.2 one-row article layout: `[number+author] [title] [page]`.
- Three equal-width columns.
- Repeating section text in all three cells.
- Loose paragraph TOC generation.
- Manual page numbers before final render.


## v2.4 full-release page and author rules

- Do not detect article start pages by the first occurrence of an article title in the rendered PDF: the title also appears inside the TOC. Page detection must exclude TOC page occurrences by starting after the TOC block/body-start page or by requiring article-front-matter evidence such as UDC/DOI near the title.
- TOC author text must be supplied by `naukainfo-toc-author-cleaning`; never concatenate all `AUTOR` paragraphs without filtering.
- If a same-section block contains multiple articles, the section row is printed once, while each article still receives its own page break.

## v2.9 final-source rule

Never retain author rows from an earlier TOC. After final `AUTOR`/`pip` classification, rebuild the complete TOC table from body styles and then run `audit_toc_author_sync.py`.

## v3.0 free-listener tail section

After all article sections, invoke `naukainfo-free-listener-toc-section`. When listeners exist, append the exact published `SPECIAL THANKS FOR ACTIVE PARTICIPATION IN THE SCIENTIFIC AND PRACTICAL CONFERENCE ARE EXTENDED TO THE FOLLOWING PARTICIPANTS:` heading as one merged `TabSEC` row and then exactly one `TabPIP` names row in the same table. Join all names with comma + space in manifest order; keep number and page cells empty. A separate page or one row per listener is a release defect.
