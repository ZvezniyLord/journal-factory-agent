---
name: naukainfo-multi-article-assembly
description: Assembles multiple already-validated NAUKAINFO articles into one ETALON journal while preserving section order, article-start page breaks, objects, and independent reference numbering restarted at 1 for every article. Use after single-article style/layout QA and before final TOC materialization.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; docxcompose; NAUKAINFO Journal Builder project.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Preconditions

- Every input article has already passed canonical style, table/figure, spacing, shape and reference-block QA.
- Article order and official English section names are confirmed from the manifest/section library.
- `ETALON-JOURNAL.docx` is read-only and the output is a new workspace copy.

# Procedure

1. Extract only the article body range: first `SECTION` paragraph through the last `REFER` entry. Never append another copy of the cover, service pages or protected tail.
2. Preserve full OOXML package relationships for tables, images, SmartArt, shapes, textboxes and numbering; do not merge as plain text.
3. Insert articles in manifest order before the protected tail section. Add `pageBreakBefore` to every article/section after the first so every article starts on a new page.
4. Keep a section heading only once before the first article of each non-empty section. When consecutive articles belong to the same section, omit repeated `SECTION` paragraphs.
5. After composition, rebuild each reference block independently:
   - one fresh `w:num` instance per article;
   - `w:startOverride=1`;
   - one `numId` inside the block and a different `numId` for the next article;
   - remove copied `w:tabs`, direct `w:ind`, foreign numbering and character overrides.
6. Reopen and audit exact paragraph/table text sequence against every source article. A change in text, row/cell structure or object signature is a hard failure.
7. Render the assembled journal. Determine actual internal start pages only after pagination stabilizes, then materialize the static TABLE OF CONTENTS.
8. Re-render all pages. Confirm that the protected final service page is last and that no extra blank page was created by appended section properties.

# Mandatory gates

- Each reference block visibly starts with `1.` and structurally uses a distinct `numId` with start override 1.
- Every article starts on a new page.
- Exact source text/table sequence is unchanged.
- SmartArt/diagram relationship parts and source media hashes are preserved.
- Only `SECTION`, `AUTOR` and `Назва1` have TOC outline levels.
- No appended body-level or paragraph-level section artifacts create a blank trailing page.

# What worked

- Trimming styled single-article ETALON copies to the semantic article range before composition.
- `docxcompose` for relationship/media import, followed by targeted section-artifact cleanup.
- Fresh numbering instances after the final merge, not before it.
- Two-pass TOC: render first, then insert actual start pages and render again.

# What did not work and must not be reused

- Appending complete single-article journals, which duplicates covers and tail pages.
- Trusting source `numId` values after composition; they may be remapped or continue across articles.
- Generating TOC page numbers before final pagination.
- Accepting object counts without exact text/table signatures and full-page visual QA.

# Done when

The merged DOCX passes structural/content/style/reference audits and every rendered page is inspected at 100% zoom.

## v2.1 addition: static TOC page numbers
When building a multi-article draft, insert the static table of contents at the existing `TABLE OF CONTENTS` location, render the DOCX to PDF/PNG, locate actual article start pages, then update TOC page numbers and render again. Internal page number = physical PDF page minus the unnumbered front matter offset. For current NAUKAINFO journal shell, the offset is 2.

The final TOC must include section heading, article number + author(s), article title, and verified starting page.
