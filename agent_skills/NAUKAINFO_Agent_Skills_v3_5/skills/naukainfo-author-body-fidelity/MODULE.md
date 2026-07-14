---
name: naukainfo-author-body-fidelity
description: Highest-priority NAUKAINFO publishing skill. Preserves the author's article body text, paragraph order, lists, tables, figures, formulas, captions, notes, and object structure one-to-one while allowing only explicitly approved journal normalization. Must run before and after every formatting, merge, pagination, or style operation.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; lxml; NAUKAINFO Journal Builder project.
metadata:
  author: naukainfo
  version: "1.0.0"
  priority: "0-critical"
---

# Non-negotiable principle

The author body is the source of truth. Do not rewrite, paraphrase, shorten, expand, reorder, “improve,” translate, or silently correct the scientific text. The target is:

- **100% lexical preservation of the article body**, except explicitly approved label-only normalizations;
- **at least 99% structural preservation** of paragraphs, lists, tables, figures, formulas, captions, notes, and object order;
- when layout convenience conflicts with author-content fidelity, **author-content fidelity wins**.

# Scope

The protected author body begins after the article title/required blank and includes annotation/abstract, keywords, main text, all lists, tables, drawings, SmartArt/shapes, formulas, captions, notes/sources, conclusions, and bibliography entries. UDC/DOI and the author header are service metadata and follow separate skills, but their removal or normalization must never shift or delete body content.

# Allowed changes only

1. Set the approved font size and line spacing.
2. Assign canonical template styles to recognized semantic roles without changing visible wording or order.
3. Normalize only the labels explicitly defined by business rules: `Анотація.` / `Abstract.`, `Ключові слова:` / `Keywords:`, reference stamp, `URL:` / `DOI:` prefixes.
4. Remove personal contact data from the author header only, without blank holes.
5. Normalize service metadata grammar in the author header only.
6. Apply approved UDC/DOI insertion, table/figure spacing, first-line-indent fixes, and pagination repair that do not alter the body text or object order.
7. Reconstruct bibliography numbering only inside the reference block; bibliography entry wording must remain intact.

Anything else requires an explicit operator decision recorded in the audit trail.

# Body-list preservation rule

- A manually typed body list (`1.`, `2.`, `-`, `•`, arrows, letters) remains manually typed unless the user explicitly authorizes conversion.
- An automatic Word list remains automatic and retains its numbering semantics.
- Never convert a manual body list into automatic numbering merely for visual neatness.
- Reference lists are the only default exception because `REFER` requires fresh per-article numbering from 1.

# Procedure

1. Snapshot the raw article before editing:
   - ordered paragraph texts;
   - paragraph/list markers and numbering mode;
   - tables with row/cell text and merge map;
   - drawings, SmartArt, shapes, textboxes, equations, footnotes/endnotes and captions;
   - object order and relationship/media signatures.
2. Classify every intended change as `allowed`, `operator-approved`, or `forbidden`.
3. Apply only allowed/approved transformations.
4. Reopen the output and run structural comparison against the raw source.
5. Report separately:
   - lexical body match;
   - paragraph/order match;
   - table/cell match;
   - list-mode match;
   - object/formula match;
   - approved differences.
6. Render every page and visually inspect body flow, tables, lists, drawings, captions and page breaks.
7. Fail the build if any unapproved body change exists.

# Mandatory gates

- `body_text_unapproved_changes == 0`.
- `body_structure_similarity >= 0.99`.
- paragraph and table order unchanged.
- no missing/extra table rows or cells.
- no missing/extra figures, formulas, SmartArt/shapes or captions.
- body manual-vs-automatic list mode unchanged, except references.
- every difference is listed in `approved_transformations` with the rule that authorized it.
- full render QA passed.

# What worked

- Source/final semantic signatures compared after every major operation, not only after final merge.
- Separating service metadata normalization from the protected author body.
- Treating manual body list markers as author text instead of “fixing” them into Word numbering.
- Whitelisting allowed transformations and failing closed on everything else.

# What did not work and is removed from active logic

- “Visually similar” acceptance without text/structure signatures.
- Rebuilding body paragraphs from extracted plain text.
- Automatic grammar or stylistic rewriting of the article body.
- Converting all detected lists to automatic numbering.
- Using object counts alone as proof of fidelity.

# Done when

The source-to-final audit shows no unapproved lexical changes, at least 99% structural fidelity, exact table/list/object order, and every rendered page has passed visual review.

## v2.1 addition: body lists are author structure
Lists inside the body of an article are treated as author structure. They must not be converted between manual and automatic numbering unless the block is identified as the references block. Only `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` is rebuilt with canonical independent numbering. Body lists, even if visually imperfect, stay as the author created them unless the user explicitly asks to normalize them.

## v2.9 non-text extension

The protected author body includes media bytes, object order, captions, subheading emphasis, list-definition semantics, tables, formulas, and author count—not only extracted paragraph text. Any missing image or coauthor is a hard failure.

## v3.0 run-emphasis fidelity

Body integrity includes run-level bold, italic, underline, small caps, superscript/subscript, and paragraph alignment. Scientific subheadings such as `Вступ`, `Мета дослідження`, `Матеріали та методи`, `Результати та їх обговорення`, and `Висновки` must retain the source emphasis unless a canonical marker rule explicitly overrides it. Compare source/final emphasis signatures per paragraph and fail on unexplained loss.
