---
name: naukainfo-reference-entry-reconstruction
description: Reconstructs logical bibliography entries when authors typed numbers manually, used Enter inside one citation, mixed manual/automatic numbering, or pasted formatted hyperlinks. Use before canonical REFER numbering and reference-block fidelity.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; OOXML/python-docx; NAUKAINFO Jurnal.dotx.
metadata:
  author: naukainfo
  version: "1.1.0"
---

# Why

A source bibliography may display `1., 2., 3.` but the digits can be typed characters rather than Word numbering. An author may press Enter inside one citation, producing continuation paragraphs that would otherwise become false new entries. The final list must preserve citation text while becoming a clean Word list.

# Boundary detection

Treat a paragraph as a new entry when at least one reliable signal exists:

- Word `numPr` automatic numbering;
- a leading manually typed number such as `1.`, `1)`, `(1)`;
- an already validated `REFER` paragraph.

An unnumbered paragraph following a detected entry is a continuation and is joined to the previous entry with one space. Remove the redundant paragraph. If no reliable boundaries exist for a multi-paragraph bibliography, stop with `REFERENCE_BOUNDARIES_AMBIGUOUS` for operator review; never merge everything silently.

# Cleanup equivalent to Ctrl+Space

After reconstruction, rebuild the complete entry as plain template text before assigning `REFER`:

- remove imported character styles, shading, highlighting, underlining and hyperlink blue;
- remove foreign direct tabs/indents and source `numId`;
- retain the exact textual content;
- assign a fresh per-article numbering instance with `startOverride=1`.

# URL and DOI labels

- Every ordinary `http://` or `https://` link must be immediately preceded by `URL: `.
- A DOI URL (`https://doi.org/...` or `http://dx.doi.org/...`) and a bare DOI identifier (`10.xxxx/...`) must be immediately preceded by `DOI: `.
- Normalize duplicated or wrong labels (`URL: DOI:`, `URL: https://doi.org/...`) to the correct single label.
- A DOI label is valid and is not replaced with URL.

# QA

- Compare reconstructed entry count and concatenated citation text with source evidence.
- Check each article’s first visible reference number is 1 and that `numId` is distinct between articles.
- Assert no manual leading numeral remains in entry text.
- Assert all web/DOI strings have the correct label.
- Render every reference page and inspect hanging alignment.

Implemented in `scripts/finalize_business_semantics.py`.


# v1.1 duplicate-number prevention

- Never accept a paragraph merely because the `REFER` style is selected. Inspect visible entry text and `w:numPr` after save/reopen.
- A final `REFER` paragraph with automatic numbering must not begin with a typed numeral (`1`, `1.`, `1)`, `(1)`, etc.). This is a hard failure `REFERENCE_DUPLICATE_NUMBER`.
- One logical source entry must become one `REFER` paragraph. Do not collapse several manually numbered citations into one paragraph.
- Compare the final entry count to source evidence and compare concatenated citation text after removing only source numbering tokens. Count mismatch or text mismatch blocks release.
- Regression fixture: Skripnyk Oleksandr Viktorovych contains nine manually numbered source entries; final output must contain nine separate automatically numbered `REFER` paragraphs with no typed leading digits. The fixture is evidence only; production logic remains generic.
