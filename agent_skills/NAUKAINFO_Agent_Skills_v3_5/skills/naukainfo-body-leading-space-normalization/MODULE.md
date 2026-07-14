---
name: naukainfo-body-leading-space-normalization
description: Removes author-created leading spaces or tabs used as fake paragraph indents while preserving the text, paragraph order, and real author formatting.
license: Proprietary project skill
compatibility: Word DOCX/OOXML; NAUKAINFO Journal Builder; Дирежор project only.
metadata:
  author: naukainfo
  version: "3.0.0"
---

# Scope

Some authors simulate a first-line indent by typing multiple spaces or tabs at the beginning of body paragraphs. These characters create unstable layout after style normalization and must be removed without rewriting the sentence.

# Rules

1. Inspect the first visible text node of ordinary body paragraphs, including paragraphs inside textboxes.
2. Remove only leading spaces, non-breaking spaces, and tabs used before the first lexical character.
3. Do not collapse internal spaces, punctuation, equations, code, tables, reference URLs, or intentional alignment inside figures.
4. Delete a paragraph only when it contains no object and consists solely of spaces/tabs, and only if it is not a required business blank.
5. Apply the canonical paragraph/style indent after character cleanup.
6. Compare source/final lexical text after excluding the removed leading whitespace only.

# QA

Fail if a paragraph still begins with 2+ layout spaces/tabs outside an allowed preformatted block, or if any non-whitespace character was removed.

# Worked

Sherbon-type English body paragraphs: remove fake space indentation while retaining wording, emphasis, and paragraph boundaries.

# Removed from active logic

Global whitespace normalization across the whole article, which can damage references, equations, tables, and author punctuation.
