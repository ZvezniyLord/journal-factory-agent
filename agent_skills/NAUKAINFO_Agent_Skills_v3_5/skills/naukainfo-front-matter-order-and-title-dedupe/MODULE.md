---
name: naukainfo-front-matter-order-and-title-dedupe
description: Normalize article front matter to UDC/DOI -> author header -> title, merge split titles, and prevent duplicated titles.
---

# Front Matter Order and Title Deduplication

## Canonical order
Every article must be transformed into this order before body processing:
1. optional DOI line;
2. UDC/УДК line;
3. author block: `AUTOR` + `pip` lines;
4. exactly one blank paragraph;
5. article title with style `Назва1`;
6. exactly one blank paragraph;
7. article body beginning with annotation/keywords or the first body paragraph.

## Non-standard source orders
The source may use:
- UDC -> title -> header;
- title -> header -> no UDC;
- UDC -> header -> title;
- split title across multiple adjacent paragraphs.

The builder must semantically identify UDC, author block, title and body, then output only the canonical order.

## Split titles
If the title is broken into multiple adjacent title-like paragraphs, merge them into one `Назва1` paragraph, preserving the exact words in their original order.

## Duplicate-title prevention
After the canonical title is emitted, the original title paragraph(s) from the source must not be copied again into the body.
Before final delivery, run a duplicate-title scan:
- for every `Назва1`, find the next non-empty paragraph;
- if it equals the title text and is not the annotation/keywords/body, delete the duplicate;
- log the deletion as a generator-regression fix.

## Spacing
- Exactly one blank paragraph must appear between the last header line and the title.
- Exactly one blank paragraph must appear after the title.
- More or fewer blank paragraphs are invalid.

## What worked
- Canonical reorder stage before body copy.
- Duplicate scan after assembly.

## What did not work and is removed from active logic
- Setting `body_start_idx` manually without excluding the original title paragraph.
- Assuming the title always appears in the same source order.


# v1.1 anti-regression rules

- Canonical frontmatter order is **DOI/UDC → author header → article title → annotation/abstract**.
- Do not insert a new title if a source title already exists; move/style the existing title instead.
- If the title was originally before the header, move it below the cleaned header and add exactly one blank paragraph before the title and one after it.
- Title dedupe must compare normalized text, including collapsed spaces and removed line breaks.
- Header cleanup must finish before TOC rebuilding, because the TOC author line is derived from `AUTOR` paragraphs.
