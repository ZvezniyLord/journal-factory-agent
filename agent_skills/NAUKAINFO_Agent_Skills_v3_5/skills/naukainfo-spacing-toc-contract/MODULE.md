---
name: naukainfo-spacing-toc-contract
description: Enforces NAUKAINFO blank-line spacing around article titles, figures, tables, source notes, and reference blocks, and guarantees only section, author names, and article titles enter the TOC outline.
---

# NAUKAINFO spacing + TOC contract

Use after semantic styling and before final render.

## Blank-line rules

- Insert exactly one empty paragraph after each article title (`Назва1`) before the annotation or body text.
- Insert exactly one empty paragraph after a figure caption (`РисПід`) when there is no separate source note below it.
- If a figure/table has a source note (`Джерело:` / `Source:`), treat the source note as the closing part of that figure/table block and insert exactly one empty paragraph after the source note.
- Insert exactly one empty paragraph after every table block. If the table has a source note, the empty paragraph goes after the source note, not between the table and the source note.
- Insert exactly one empty paragraph before and after the canonical reference stamp `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`.

## TOC/outline contract

Only these roles may have outline levels for automatic TOC generation:

1. section heading: `SECTION`;
2. author full name: `AUTOR`;
3. article title: `Назва1`.

Author metadata (`pip`), DOI/UDC, annotations, keywords, figure/table captions, source notes, table text, references, and ordinary body text must not have outline levels, heading styles, or inherited heading behavior.

## Regression rule

If a previous method only made the page visually similar but left `pip` or ordinary text as a heading/outline item, remove that method from the pipeline and replace it with structural OOXML style/outline checks.
