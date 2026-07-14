---
name: naukainfo-author-header-cleanup
description: Cleans and grammatically normalizes the author header before the article title: removes email/phone/messenger contacts without blank holes, preserves ORCID, routes names/metadata to canonical styles, and lowercases Ukrainian role/common-noun lines. Use before title/body normalization.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; OOXML/python-docx; NAUKAINFO Jurnal.dotx.
metadata:
  author: naukainfo
  version: "1.2.0"
---

# Scope

The header is the range after DOI/UDC and before the article title.

# Contact cleanup

- Remove personal email addresses, phone numbers and Telegram/Viber/WhatsApp contact lines.
- ORCID is allowed and must be preserved.
- If a paragraph contains both useful metadata and contact data, remove only the contact token/label and retain the meaningful remainder.
- If the paragraph becomes empty, delete it completely. Do not leave an empty paragraph or double gap.
- Contact removal is permitted editorial cleaning and is not `critical_text_loss`.

# Grammar and capitalization

- Human names use `AUTOR` and retain proper-name capitalization.
- After a mixed author line is split, the standalone person-name paragraph must not end in `,`, `;`, or `:`. Remove only this terminal service punctuation when metadata continues on following `pip` lines; preserve initials, apostrophes and internal hyphens.
- Degree, status, position, institution, city/country and ORCID use `pip`.
- Ukrainian common-noun role/status lines begin with lowercase: `студент`, `студентка`, `здобувач`, `здобувачка`, `аспірант`, `кандидат наук`, `доцент`, `професор`, `керівник`, etc., unless the word begins a full sentence rather than a metadata line.
- Do not invent or expand degrees, positions or affiliations.
- `pip` must have no outline level and must never enter the TOC.

# QA

1. Scan header text for email/phone/contact labels; expect zero prohibited contacts.
2. Confirm ORCID remains.
3. Confirm no blank paragraph was introduced where a contact was deleted.
4. Compare all non-contact header text with the source; terminal punctuation removed from a standalone name is logged as allowed business normalization.
5. Assert exact style IDs and render the header.

Two real project-derived fixtures with contacts are maintained under `tests/fixtures/`.


# v1.1 additions: frontmatter hygiene and contacts

- Remove author-supplied section notes such as `Секція 013 – ...` from the article body/frontmatter; real journal sections are inserted only by the builder as `SECTION` rows.
- Remove personal emails even when they are split or partially damaged by previous processing. Examples: `name@gmail.com`, `name @ ukr.net`, and leftover fragments from email paths such as `nv/`.
- If an `AUTOR` paragraph contains a comma followed by degree/position data, split it into:
  - author name only → `AUTOR`;
  - degree/position/affiliation remainder → `pip`.
- If the source order is `UDC → title → header`, reorder front matter to the journal contract `UDC/DOI → header → title`; record this as allowed frontmatter normalization, not body rewriting.
- Never move or rewrite paragraphs after `Анотація.` / `Abstract.` as part of header cleanup.


# v1.2 hard gates: author punctuation, UDC and frontmatter geometry

- Run the terminal punctuation cleanup over **all** standalone `AUTOR` paragraphs, not only paragraphs that were split during the current pass. The same rule applies to author-name text in TOC cells.
- After DOCX save/reopen, assert that no standalone author name ends in comma, semicolon or colon. A style label alone is not proof.
- The required sequence is `DOI (optional) → UDC/УДК → exactly one blank → AUTOR/pip header → exactly one blank → title → exactly one blank → annotation/body`.
- When UDC/УДК is missing, classify the article by subject and insert a documented high-confidence proposal as actual `UDC`. Store `udc_source=generated` and the evidence phrase. If classification is ambiguous, return `UDC_REVIEW_REQUIRED`; never silently omit UDC.
- Strip `w:numPr`, bullets, tabs, left/first-line/hanging indents and imported outline levels from DOI, UDC, AUTOR, pip and title paragraphs. Re-open and verify the OOXML properties, then render the header.
- Every degree, role, department, institution, city, country and ORCID line in the header must be actual `pip`; unidentified helper text is a release defect, not acceptable `Normal` text.
