# EDITORIAL_RULES.md
## NAukaInfo editorial and production rules

### 1. Purpose
These rules define the NAukaInfo business/editorial layer and govern participants, journal structure, formatting, contacts, TOC, references and authenticity.

## 2. Excel registry
Excel is the registry/business source of truth for participant existence, order, material title, section, services, DOI request/status, printed-copy flags and free-listener status.

Build `manifest.json` with at least:
- internal id;
- Excel row/order;
- author names and coauthors;
- original and normalized title;
- section id/name;
- matched source file and confidence;
- questionnaire/application file;
- free_listener;
- doi_requested;
- printed_copy;
- qa_status;
- warnings.

### Coauthors
Do not create duplicate articles for coauthors. Group coauthors under one material. Ambiguity becomes a review item.

### Free listeners
Free listeners:
- do not receive fabricated articles;
- are not counted as publication materials;
- appear only in the dedicated `SPECIAL THANKS` / participation block.

### Questionnaires/applications
Use as secondary metadata sources for full name, affiliation, degree/position, supervisor, contacts, ORCID and matching evidence. If Excel and questionnaire conflict, do not guess; create an audit issue unless an explicit field rule resolves it.

## 3. Front matter — immutable
Everything before `TABLE OF CONTENTS` is immutable during an ordinary build.

No:
- font normalization;
- size changes;
- spacing changes;
- indent changes;
- style cleanup;
- paragraph restructuring;
- global `Normal` mutation;
- reflow;
- automatic rewrite.

Validate with normalized XML/hash comparison and render comparison where feasible.
Any ordinary build that changes front matter is BLOCKED.

## 4. Global body formatting
NAukaInfo defaults:
- Times New Roman;
- 11 pt;
- line spacing 1.0;
- space after 0 pt;
- first-line indent 1.0 cm.

These values come from `naukainfo.yaml`.
For explicitly configured properties: `editorial config > template`.

Do not implement this by globally changing `Normal`.
Apply body formatting only to target article-body roles after front matter.

### Tables
Default:
- 10 pt;
- 1.15 spacing;
- no first-line indent.

A more specific explicit template rule may apply only when it does not conflict with fixed editorial settings.

### Internal headings
Typical: bold, left aligned, no invented numbering.

## 5. Local author formatting must survive
Global normalization must NOT erase:
- bold;
- italic;
- underline;
- superscript;
- subscript;
- hyperlinks;
- meaningful table emphasis;
- formula formatting.

Never collapse all runs in a paragraph into one plain run.
Formatting-integrity QA must compare source -> final.

## 6. Paragraph roles
Where practical classify:
- SECTION_TITLE
- DOI
- UDC
- AUTHOR
- SUPERVISOR
- AFFILIATION
- TITLE
- ABSTRACT
- KEYWORDS
- BODY
- SUBHEADING
- TABLE_CAPTION
- FIGURE_CAPTION
- REF_TITLE
- REFERENCE
- REFERENCE_CONTINUATION
- SPECIAL_THANKS
- OTHER

Apply formatting by role, never blanket document-wide mutation.

## 7. Author header
Control:
- author names;
- degrees;
- positions;
- department;
- institution;
- city/country;
- ORCID;
- UDC/UDC;
- DOI;
- article title.

Do not arbitrarily restructure the header.
Institution is not an author.
Supervisor is not automatically a coauthor.

## 8. Scientific supervisors
Store separately:
```json
{
  "authors": [],
  "scientific_supervisors": [],
  "affiliations": []
}
```

For the built-in `NAukaInfo` profile:
`toc.include_scientific_supervisors = true`.

Supervisor:
- remains a supervisor in the article body;
- appears in TOC;
- is not converted into a coauthor.

Only an explicit run/editorial override may change this. Hermes/template inference may never change it.

## 9. Contact-removal policy
Author e-mail is NOT published.

Removing e-mail:
- is intentional;
- is not semantic text loss;
- must not be auto-restored.

Other contact types may be removed only when enabled by policy:
- phone;
- Telegram;
- Viber;
- WhatsApp;
- other private contact lines.

Contact removal must be explicit in config/audit.

## 10. UDC / УДК
If supplied, preserve it.

Format:
- Ukrainian article: `УДК ...`
- English article: `UDC ...`

One line, no brackets/quotes.

If missing:
- use deterministic/local resources where possible;
- Hermes may advise;
- final insertion must be validated and auditable.

## 11. DOI
NAukaInfo DOI prefix: `10.64828`.

Rules:
- never silently remove a DOI already present in a source;
- do not invent DOI when not requested/authorized;
- DOI policy must be configurable;
- distinguish conference DOI from article DOI;
- prevent duplicates;
- record DOI status in manifest and QA.

## 12. Sections and ordering
Section order comes from config/template.

Priority:
1. explicit Excel/manifest section;
2. configured rule;
3. semantic classification if missing;
4. low confidence => review.

Hermes may advise but may not force a low-confidence section.

One section heading per section.
Inside section default to Excel order.
Every intended article appears exactly once.
Start each article on a new page when profile/template requires it.

## 13. TOC
Generate from structured metadata + actual final article order.

Include:
- author(s);
- scientific supervisor(s) when enabled;
- article title;
- section structure;
- page number/field required by template.

Do not include affiliations as authors.
TOC order must equal body order.

# 14. REFERENCES / bibliography — release-blocking

### 14.1 Headings
Recognize:
- `REFERENCES`
- `REFERENCE`
- `ЛІТЕРАТУРА`
- `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ`
- equivalent language variants.

Prefer semantic detection, not one exact literal.

### 14.2 `REFER` must be real
A visible style label alone is insufficient.

Every real reference item must have:
- canonical `REFER` style where used;
- correct `numPr`;
- correct `numId`;
- correct `ilvl`;
- correct indents;
- correct tabs;
- correct style inheritance;
- real Word numbering.

Do not type fake visible numbers into text.

### 14.3 Independent numbering per article
Every article bibliography is an independent Word list instance.

Invariant:
- first visible reference of every article = `1`;
- no carry-over from previous article;
- use separate `numId`, `startOverride` or another technically correct restart.

### 14.4 Continuation lines
A DOI/URL or other separate paragraph may be a continuation of the previous reference.

If so it:
- stays unnumbered;
- aligns under the bibliographic text;
- does not become a new source.

Hermes may advise ambiguous cases. Deterministic code applies final structure.

### 14.5 Reference authenticity
Preserve:
- full text;
- order;
- numbering;
- hyperlinks;
- DOI;
- URL;
- bold/italic/underline;
- continuation structure.

### 14.6 Word acceptance test
Release-blocking:
1. open final DOCX in Microsoft Word;
2. click representative reference;
3. style already behaves as canonical `REFER`;
4. ruler/indent is already correct;
5. manually reapplying `REFER` should not be required;
6. first item of article 2 already shows `1`;
7. no right-click `Start at 1` repair is needed.

## 15. Tables
Preserve count, rows, columns, merged cells, text, numeric values, captions, source lines, local emphasis, alignment, borders and meaningful shading.
Do not convert tables to plain text.

Section-title cells in the TOC/table must be centered inside the cell:
- horizontal alignment: center;
- vertical alignment: center;
- no accidental left alignment after save/reopen;
- this alignment must survive Microsoft Word save-close-reopen validation.

Render-check every page with tables.

## 16. Images and drawings
Preserve images/drawings, order, aspect ratio, captions, relationships and meaningful anchoring/insertion order.
Do not distort images.
Any unexplained loss => BLOCKED.

## 17. Equations, chemistry and indices
Preserve OMML, superscript, subscript, Greek letters, special symbols, chemical indices and mathematical layout.
Loss of subscript/superscript is formatting-integrity failure.

## 18. DOC and DOCX
For DOCX preserve package relationships and objects.
Legacy `.doc`: convert a working copy to DOCX, never alter original, then verify text, tables, images, lists and formatting.

## 19. Authenticity QA
Do not define authenticity as character count only.

For every article validate:
- title;
- author block;
- paragraphs/sentences;
- abstract;
- keywords;
- body;
- subheadings;
- tables;
- captions;
- figures;
- conclusions;
- references;
- local formatting.

Allowed differences:
- configured contact removal;
- approved global font/size/spacing/indent normalization;
- generated numbering labels;
- approved technical editorial normalization.

## 20. Separate QA verdicts
Keep at least:
- Content QA;
- Formatting QA;
- Layout QA.

Do not merge into one opaque boolean.

## 21. Visual QA
XML is not enough.

Render final document and check at least:
- TOC;
- first page of every article;
- every bibliography page;
- every page with table/image;
- section transitions;
- suspicious formatting diffs;
- last page.

Look for clipping, overlaps, blank pages, orphan headings, broken numbering, missing images, table overflow and unexpected list numbers.

For formatting disputes compare source render vs final render.

## 22. Forbidden accidental numbering
No unexpected list numbers before abstract, keywords, body text, table cells, table captions, author header, affiliation or figure captions.

Validate `numPr`, `numId`, `ilvl`, style inheritance and rendered appearance.

## 23. Style conflicts
Inspect style IDs, names, `basedOn`, linked styles, numbering links and inheritance.

Use a safe remap/import strategy.
Do not change front matter to solve article-style conflicts.

## 24. No global `Normal` fix
Never normalize body by changing `Normal`.

Normalize only target roles after the immutable front-matter boundary.

## 24A. Word reopen stability — release-blocking

A journal is not stable merely because it looks correct immediately after mutation.

Before final PASS:
- canonical body styles must not contain `w:autoRedefine`;
- canonical body styles must explicitly define `ascii`, `hAnsi`, `eastAsia` and `cs` font slots;
- canonical body styles must not depend on `asciiTheme` / `hAnsiTheme` / theme-font fallbacks;
- body alignment/spacing/indent must be explicit in the intended role/style, not accidentally inherited from `Normal`;
- do not repair this by globally changing `Normal`;
- section/footer distances used by the journal body must be deliberate and validated;
- if Microsoft Word is available, perform a save-close-reopen roundtrip and compare effective formatting/rendering before release.

If the document visibly changes after a Word save/reopen, final status is BLOCKED.

## 25. Final report
`qa/report.md` must include:
- participant count;
- author count;
- material count;
- free-listener count;
- DOI count;
- matched originals;
- unmatched/review items;
- all participants accounted YES/NO;
- all materials present YES/NO;
- semantic text loss YES/NO;
- tables/images/formulas/references preserved YES/NO;
- bibliography restart verified YES/NO;
- formatting integrity PASS/WARN/FAIL;
- front matter unchanged YES/NO;
- TOC correct YES/NO;
- visual render checked YES/NO;
- concrete issues;
- allowed editorial differences;
- final release status.
