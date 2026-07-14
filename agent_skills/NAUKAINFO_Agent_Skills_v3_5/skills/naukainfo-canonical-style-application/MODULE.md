---
name: naukainfo-canonical-style-application
description: Inserts the verified English-only section heading once before the first article of a section and structurally applies the canonical ETALON paragraph styles to UDC/DOI, author names, author metadata, article titles, drawings, figure captions, table cells, reference headings, and reference entries. Use after article insertion and before pagination/visual QA.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; NAUKAINFO ETALON styles; Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "2.0.0"
---

# Purpose

A visually similar article is not sufficient. The final DOCX must contain the actual ETALON styles so later TOC, pagination, audits and automated editing can rely on structural semantics.


# Authoritative style-source rule

Never recreate `SECTION` or any canonical style by visual approximation. Copy the exact style node and its base-style chain from the user-supplied `Jurnal.dotx`. For the verified template, `SECTION` is centered, Times New Roman 24 pt, bold, all caps, 18 pt after, based on Heading 1 and outline level 1 through inheritance. Preserve `pip` as non-heading metadata.

# Section rule

1. Resolve `section_id` from the validated manifest.
2. Resolve the official English label from the project section library; never translate ad hoc.
3. Insert the label once, immediately before the first article in that section.
4. Do not repeat it before subsequent articles of the same section.
5. Do not create empty sections.
6. Apply style `SECTION` and keep it with the following UDC/DOI block.
7. Section headings inside the journal body are English-only.

Verified mapping used for conference 136 article `Гнисюк`: section 1 → `ECONOMIC THEORY, MACRO- AND REGIONAL ECONOMY`.

# Canonical ETALON style map

| Semantic role | Required style |
|---|---|
| section label | `SECTION` |
| DOI / DOI URL | `UDC` |
| УДК / UDC | `UDC` |
| human author name | `AUTOR` |
| degree, role, institution, city/country, ORCID | `pip` |
| article title | `Назва1` |
| paragraph containing image/SmartArt/shape/chart | `РИС` |
| figure caption | `РисПід` |
| every paragraph inside table cells | `TABLETEXT` |
| references heading | `REF-TITLE` |
| each reference entry | `REFER` |

Annotations/abstracts and keywords are normalized by `naukainfo-annotation-keywords-normalization` as template `Normal` paragraphs with the ordinary body first-line indent; they are not headings. Table number/title and figure/source-note handling is delegated to `naukainfo-table-figure-caption-contract`; reference heading/entries are finalized by `naukainfo-reference-block-fidelity`.

# Procedure

1. Work on a copy of ETALON.
2. Identify the article range after `TABLE OF CONTENTS` and before the protected tail section.
3. Insert the section heading from the manifest/library.
4. Classify article front matter and assign styles from the map.
5. Preserve text, run emphasis, numbering XML, hyperlinks, drawings, SmartArt relationships, merged cells and author alignment.
6. Remove conflicting direct font-size/bold overrides only when they prevent the canonical style from rendering as defined.
7. Apply `TABLETEXT` to every visible table-cell paragraph, including merged/nested cells, without flattening header alignment or emphasis.
8. Reopen the saved DOCX and assert actual style names, not visual similarity.
9. Run semantic-indent, table-fidelity, shape-fidelity and content-integrity audits.
10. Render every page and inspect section, front matter, figures, tables, references and protected tail.

Use `scripts/finalize_business_semantics.py` as the authoritative deterministic implementation; the earlier visual-approximation style script was removed.

# Stop conditions

Stop for review if the section label is not in the official library, the article title or author boundary is ambiguous, style assignment changes numbering/TOC unexpectedly, or any object/text is lost.

# Done when

The section appears once in English, every required paragraph has the exact canonical style, no protected role has a positive first-line indent, article content/object counts match the source, and rendered pages pass visual QA.
