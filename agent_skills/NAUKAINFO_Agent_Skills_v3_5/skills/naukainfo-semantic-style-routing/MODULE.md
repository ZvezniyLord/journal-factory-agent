---
name: naukainfo-semantic-style-routing
description: Classifies article paragraphs by semantic role, preserves Normal body indentation for prose/annotation/keywords, and applies zero positive first-line indent only to service metadata, author/title/object/table/list/reference roles while preserving numbering, hanging indents, and source fidelity.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; NAUKAINFO ETALON styles; Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "2.0.0"
---

# Purpose

`ETALON-JOURNAL.docx` defines a 1 cm first-line indent in `Normal`. Paragraphs copied from an article can silently inherit that indent even when the original has none. This skill identifies paragraph roles before final assembly and prevents the template body indent from leaking into service and object-related text.

# Canonical semantic roles

## No positive first-line indent

The following roles must have an effective first-line indent of zero:

- DOI and DOI URL;
- `УДК` / `UDC`;
- author names, scientific degrees, positions, institutions, city/country and ORCID lines;
- article title;
- paragraphs that contain an image, SmartArt, shape group, chart or other drawing object;
- figure captions and figure source notes;
- table number, table title, table source/note;
- every paragraph inside every table cell, including nested tables;
- bulleted and numbered list items: the marker/list geometry is preserved, but a positive body-style first-line indent is forbidden;
- reference-list heading;
- reference entries: no positive first-line indent; an intentional hanging indent for numbering is allowed and must be preserved.

## Normal body paragraphs

Ordinary article body paragraphs, annotation/abstract paragraphs and keywords paragraphs use the authoritative `Normal` style and its ordinary first-line indent. The annotation/keywords labels are normalized separately by `naukainfo-annotation-keywords-normalization`. Do not remove body indentation globally. Section and author/title formatting follows the exact template style nodes.

# ETALON style map

After article insertion, assign the existing template styles structurally. Visual similarity without the correct style ID is a regression. Use the styles below after their side effects are validated:

| Semantic role | Canonical style | Rule |
|---|---|---|
| section name | `SECTION` | once before the first article of a section |
| UDC/УДК | `UDC` | left, bold, zero first-line |
| author name | `AUTOR` | preferred mapping; verify outline/TOC behavior |
| author details | `pip` | preferred mapping; verify outline/TOC behavior |
| article title | `Назва1` | centered title/TOC source |
| figure object paragraph | `РИС` | centered, zero first-line |
| figure caption | `РисПід` | use only if its bold/center formatting matches the publication contract |
| table cell paragraph | `TABLETEXT` | zero first-line; never flatten header alignment |
| reference heading | `REF-TITLE` | centered, bold, uppercase |
| reference entry | `REFER` | preserve numbering and hanging geometry |

A style name is not enough. After assignment resolve effective formatting, reopen the DOCX, and render. If a style changes alignment, numbering, outline level, TOC membership or emphasis beyond the contract, keep the source style and apply a narrow direct zero-indent override instead.

# Deterministic procedure

1. Work on a workspace copy.
2. Detect the article content range between `TABLE OF CONTENTS` and the protected tail section.
3. Classify paragraphs with exact signals: DOI/UDC prefixes, article-title structure, annotation/keyword prefixes, drawing XML, `Рис.`/`Figure`, `Таблиця`/`Table`, source-note prefixes, list numbering XML, and reference-heading markers.
4. Apply a direct zero first-line override only to protected roles; never apply it to annotation/abstract or keywords.
5. Preserve `w:numPr`, list markers and hanging indents. If a reference already has `w:hanging`, do not add a conflicting `w:firstLine`.
6. Apply zero first-line to every table-cell paragraph recursively.
7. Reopen and audit after save.
8. Render every page and inspect all figure, table, list and reference pages.

Use `scripts/semantic_paragraph_roles.py` for the deterministic classification, repair and JSON audit.

# Stop conditions

Stop for operator review when:

- article boundaries or title cannot be identified reliably;
- a style assignment would change TOC/outline behavior unexpectedly;
- a paragraph may be either body text or a caption/reference;
- reference numbering or list markers change;
- drawings/tables move, clip or split poorly after the repair;
- any protected role retains a positive effective first-line indent.

# Done when

All protected roles have zero effective first-line indent, prose/annotation/keywords keep the intended Normal indent, list/reference numbering is stable, tables and drawings are unchanged, and the full render passes visual QA.
