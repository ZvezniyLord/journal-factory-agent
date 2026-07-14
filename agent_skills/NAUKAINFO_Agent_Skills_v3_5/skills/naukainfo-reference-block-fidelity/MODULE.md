---
name: naukainfo-reference-block-fidelity
description: Normalizes each article's references block to the NAUKAINFO stamp, exact ETALON REF-TITLE/REFER styles, fresh per-article numbering, and correct hanging-indent geometry. Use after article insertion and before pagination/TOC generation.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; NAUKAINFO ETALON numbering; Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "2.0.0"
---

# Purpose

A paragraph can show style `REFER` yet still render incorrectly because copied direct indentation, tabs or a foreign `numId` override the ETALON definition. This skill makes the references block structurally correct, not merely visually similar.

# Canonical stamp

For Ukrainian articles the heading is exactly:

`СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`

Do not use `СПИСОК ВИКОРИСТАНОЇ ЛІТЕРАТУРИ`, `ЛІТЕРАТУРА`, or author-specific variants.

# Spacing contract

1. Exactly one empty paragraph before the stamp.
2. Exactly one empty paragraph between the stamp and reference entry 1.
3. Stamp uses actual style `REF-TITLE`, centered, bold as defined by ETALON, 11 pt, single, first-line indent 0, and keep-with-next.
4. No positive first-line indent is allowed in the stamp.

# Reference-entry contract

1. Every entry uses actual style `REFER`.
2. Each article has a fresh numbering instance restarted at 1; do not reuse a foreign/source `numId` or continue numbering from another article.
3. Remove direct `w:ind` and direct tab stops that override the style/numbering geometry.
4. The ETALON numbering definition supplies decimal `%1.` with left/hanging geometry of 567 twips (approximately 1 cm).
5. Entries are 11 pt, single, justified, with 0 pt before/after.
6. Continuation lines align on the text line, not under the numeral; no bullet glyphs or arrow/tab artifacts may appear.
7. Preserve reference text and language, but clear imported character formatting equivalent to `Ctrl+Space`; hyperlink underline/color, shading and foreign character styles are not preserved.
8. Reconstruct manual numbering and Enter-split continuation paragraphs through `naukainfo-reference-entry-reconstruction`.
9. Prefix ordinary web links with `URL: ` and DOI URLs/bare DOI identifiers with `DOI: `.

# Procedure

1. Detect the article references boundary before the protected tail/article break.
2. Replace the heading text with the canonical stamp.
3. Normalize surrounding blank paragraphs.
4. Create a fresh numbering instance based on the verified ETALON reference abstract numbering definition and restart it at 1.
5. Apply `REFER`, remove conflicting direct indents/tabs/foreign numbering, and attach the fresh `numId`.
6. Reopen and assert heading/style/blank spacing/numbering/direct-indent invariants.
7. Render all reference pages and visually compare the hanging alignment with a published NAUKAINFO PDF/template.

Use `scripts/finalize_business_semantics.py` as the authoritative finalizer. `normalize_captions_references.py` remains only as a lower-level compatibility utility and is not the acceptance gate.

# Stop conditions

Stop if entries cannot be reliably separated, the template reference numbering definition is missing, or the source contains mixed bibliography subsections requiring editorial judgment.

# Done when

The canonical stamp is present once, spacing is exact, numbering restarts at 1, every entry is `REFER`, no conflicting direct indent remains, and rendered continuation lines align correctly.

## v3.0 unmarked terminal bibliography inference

When an author omits a heading such as `Література`/`References`, inspect the terminal article block conservatively. Infer a references block only when all strong signals hold: it is at the end of the article; it contains at least two consecutive citation-like entries or one citation-like entry with clear bibliographic/URL/DOI evidence; numbering is manual or automatic; and the block is separated from the final body/conclusion. Insert the language-appropriate canonical stamp and apply fresh `REFER` numbering from 1. If evidence is ambiguous, stop for operator review rather than reclassifying body text.
