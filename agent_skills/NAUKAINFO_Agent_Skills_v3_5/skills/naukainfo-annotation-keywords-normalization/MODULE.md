---
name: naukainfo-annotation-keywords-normalization
description: Normalizes Ukrainian and English annotation/abstract and keywords opening labels without changing the article meaning: ordinary Normal paragraph geometry, bold label only, canonical punctuation, and language-aware first-letter casing. Use after title/style application and before content-integrity QA.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; OOXML/python-docx; NAUKAINFO Jurnal.dotx.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Annotation / abstract contract

1. The annotation is normally the first non-empty body paragraph after the article title and the required one blank paragraph.
2. Ukrainian canonical opening: **`Анотація.`** followed by exactly one space and body text beginning with an uppercase letter.
3. English canonical opening: **`Abstract.`** followed by exactly one space and body text beginning with an uppercase letter.
4. Only the opening label is bold. The annotation body is regular.
5. The paragraph uses the authoritative template `Normal` style (`a0` in the verified template), not a heading style. It retains the ordinary body first-line indent and must not enter the TOC.
6. Normalize variants such as `Анотація:`, `АНОТАЦІЯ`, `ABSTRACTS.`, or `ANNOTATION:` without rewriting the body.

# Keywords contract

1. Ukrainian canonical opening: **`Ключові слова:`** followed by exactly one space.
2. English canonical opening: **`Keywords:`** followed by exactly one space.
3. Only the label is bold. The keyword sequence is regular.
4. The first keyword starts with a lowercase letter unless the first token is an acronym/proper code that is conventionally uppercase (AI, HR, NATO, UDC, etc.).
5. The paragraph uses template `Normal`, is not a heading, and must not enter the TOC.
6. Preserve the author’s keyword sequence and punctuation except the required label/punctuation/casing repair.

# QA

- Compare source and final body text after removing only the normalized label punctuation/case.
- Assert one blank paragraph after the title and no unexpected blank between annotation and keywords.
- Inspect run properties: label run bold; body run not forced bold.
- Render the first page of every article and verify visual indentation and label emphasis.

Use `scripts/finalize_business_semantics.py` as the deterministic implementation.

## v3.0 exact adjacency

Treat annotation/abstract and keywords as one front-body cluster: annotation is immediately followed by keywords with zero empty paragraphs. Insert exactly one empty paragraph after the complete keywords paragraph before the first ordinary body paragraph. This overrides any source blank between annotation and keywords while preserving all lexical content.
