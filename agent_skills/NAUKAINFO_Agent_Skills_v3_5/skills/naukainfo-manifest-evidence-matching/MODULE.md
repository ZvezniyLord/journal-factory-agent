---
name: naukainfo-manifest-evidence-matching
description: Builds an evidence-based article manifest by matching every Excel participant/article record to an exact source document using the two primary identity signals: author full name and article title. Records the source filename, extracted evidence, confidence, and unresolved conflicts. Use before normalization, styling, ordering, or journal assembly.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; DOCX/XLSX readers required.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Sources of truth

- Excel/manifest supplies expected participants, article titles, sections and ordering.
- Raw DOCX files supply author headers, titles and article content.
- Folder names and filenames are supporting clues only; they cannot replace document evidence.

# Required matching evidence

For each expected article record capture:

1. Excel row/index and expected author name(s).
2. Expected article title exactly as stored in Excel.
3. Exact source DOCX path and filename.
4. Extracted author line(s) from the DOCX.
5. Extracted article title from the DOCX.
6. Author-name match result.
7. Title match result.
8. Supporting clues, if used: folder name, filename, UDC, institution, ORCID.
9. Final status and confidence.

# Decision rule

A record is `matched` only when both primary signals agree:

- surname and given name identify the expected author or co-author;
- article title is the same after conservative normalization of case, whitespace, punctuation and line breaks.

A filename-only or folder-only match is never sufficient.

## Statuses

- `matched_exact` — author and title both agree exactly or after conservative normalization.
- `matched_reviewed` — both primary signals agree, but transliteration, initials, hyphenation or minor title punctuation required operator-reviewed normalization.
- `ambiguous` — author agrees but title conflicts, title agrees but author conflicts, or multiple source files satisfy the same record.
- `missing_source` — Excel expects an article but no qualifying source DOCX exists.
- `unregistered_source` — a DOCX appears to be an article but has no Excel record.
- `non_article` — questionnaire, receipt, certificate request or other administrative file.

# Output contract

Produce a manifest row for every expected article and a separate inventory row for every discovered DOCX. Never silently omit duplicates or unresolved files.

The report must make the reasoning auditable in plain language, for example:

`Soloviov Oleh Volodymyrovych — found in 043_9eb86041.docx because the DOCX header contains the author’s surname and given name, and the extracted title matches the Excel title after whitespace normalization.`

# Done when

- every Excel article record has a status;
- every discovered DOCX has a classification;
- exact source filenames are recorded;
- both primary signals are shown independently;
- unresolved conflicts are isolated before styling or assembly.
