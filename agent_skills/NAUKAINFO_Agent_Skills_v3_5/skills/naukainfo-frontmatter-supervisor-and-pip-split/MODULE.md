---
name: naukainfo-frontmatter-supervisor-and-pip-split
description: Splits author headers into person lines and metadata lines, recognizes scientific supervisors as people, prevents degrees/titles from receiving AUTOR style, and preserves all non-contact affiliation content.
version: "2.9.0"
---

# Person vs metadata

`AUTOR` is assigned only to a person or explicit participant name. Degrees, titles, positions, academies, cities, and affiliations use `pip`.

Examples of metadata that must not be `AUTOR`:

- `член-кореспондент НАМН України`;
- `доктор медичних наук, професор`;
- `здобувач`, `студент`, `аспірант`;
- affiliation, department, city, country.

# Scientific supervisors

Lines such as `Науковий керівник: доцент Тимонін Ю. О.` must be split:

- `Науковий керівник:` / `доцент` → `pip` as service role text;
- `Тимонін Ю. О.` → `AUTOR` because this is a person who participated in supervision/editing.

The rule is generic, not name-specific.

# Long lines

Long author header lines may be split for readability without deleting text. Move city/country/affiliation fragments to following `pip` paragraphs when this makes the header compact and readable.

# Contacts

Emails, phones, Telegram/Viber/WhatsApp and similar personal contacts are removed without leaving empty paragraphs. ORCID is preserved.


# v2.9 protected business layout

1. Detect the complete frontmatter range from DOI/UDC through the paragraph immediately before the title.
2. Classify every line as person (`AUTOR`) or metadata (`pip`). Metadata includes degrees, academic rank, job role, department, institution, city/country and ORCID.
3. Remove terminal service punctuation from standalone person names after splitting.
4. Remove all inherited list semantics and geometry (`numPr`, bullets, tabs, left/first-line/hanging indents) from the complete frontmatter range.
5. Preserve exactly one blank after UDC and exactly one blank between the last `pip` and title.
6. Post-save/reopen acceptance requires actual style IDs, zero list markers and zero unclassified nonblank frontmatter paragraphs.
