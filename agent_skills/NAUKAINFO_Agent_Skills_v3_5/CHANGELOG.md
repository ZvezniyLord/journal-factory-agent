# v3.5.0 — Article-scoped mandatory UDC detection

- Fixed the multi-article false positive where one UDC anywhere in the journal made a missing target UDC appear present.
- A DOI paragraph using the `UDC` style no longer counts as an actual UDC marker.
- Added per-`Назва1` UDC audit, target-article selection for lookup packets, and `UDC_GENERATION_NOT_RUN` fail-closed status.
- Added regression tests for a second article with missing UDC while the first article has one.

# v3.4.0 — Frontmatter recognition and reference duplicate hard gates

- Global post-save/reopen removal of terminal commas/semicolons/colons from standalone author names and TOC author cells.
- Required UDC generation path for missing classifications, with evidence logging and ambiguity block.
- Full AUTOR/pip recognition and list/indent cleanup across frontmatter.
- Exact frontmatter order and blank-paragraph contract.
- Hard rejection of automatic `REFER` numbering combined with typed leading numbers; source/final entry-count comparison.
- Added regression audit script for these gates.

# v3.3.0 — editorial corrections locked

- Replaced the obsolete `FREE LISTENERS`/one-row-per-listener model with the exact published `SPECIAL THANKS ... PARTICIPANTS:` heading inside the same TOC table.
- Listener names are one comma-separated `TabPIP` row with empty number/page cells and zero indent.
- Standalone `AUTOR` names lose terminal service punctuation after header splitting.
- Exactly one blank after the actual UDC is mandatory.
- Table-title paragraphs after `Table N`/`Таблиця N` require actual `РисПід` (`af6`).
- Reference normalization is frozen after structural PASS; narrow corrective runs must not touch accepted references.

# v3.2.0

- Added fail-closed required-assets startup gate.
- A missing ETALON/Jurnal.dotx/manifest/master skill now blocks the build.
- Added exact ETALON section, page numbering, footer, and style-ID validation.
- Added `scripts/preflight_required_assets.py`.
- Added `docs/STARTUP_ASSET_CONTRACT.md`.
- Prohibited creating replacement journals from blank DOCX when templates are unavailable.

# v3.2 — single master skill `journal`

Validation: 74 tests passed; 1 discoverable skill validated.

- Replaced 49 independently discoverable skills with one discoverable skill: `skills/journal/SKILL.md`.
- Preserved all previous skill content as internal `MODULE.md` files and retained v3.0 as backup.
- Added universal per-article deep text-integrity audit script.
- Added fail-closed rule: no author-name/article-title branches in production logic.
- Added native-source audit finding: 0 confirmed unapproved text changes across 24 articles; 1 legacy object-order case remains REVIEW.
- Added explicit distinction between lexical PASS and full text/object/run-format certification.


## v2.5 — Project scope guard

- Added `docs/PROJECT_SCOPE.md`.
- Added `naukainfo-project-scope-guard` to the skill map.
- Clarified that NAUKAINFO Agent Skills are limited to project «Дирежор» / NAUKAINFO Journal Builder.
- Removed the unsafe implicit assumption that these business rules may be applied in unrelated chats or projects.



## v2.5 - 24-article full release QA

### Added
- `naukainfo-toc-author-cleaning` for clean participant-only author cells in the static TOC.
- Full-release TOC page-detection guard: ignore title matches inside TOC pages; scan rendered body pages only.

### Worked
- PDF-accurate 3-column TOC table from v2.3.
- Two-pass render → page detection → TOC update → re-render.
- Manual clean author map for ambiguous headers with roles/institutions on adjacent lines.

### Did not work / removed from active logic
- Using the first title occurrence in the rendered PDF as the article page number. This selects TOC pages.
- Joining all `AUTOR` paragraphs for TOC author cells. This leaks roles, degrees, institutions and city lines when a source header is irregular.
# Changelog

## v2.0 — Priority-0 author-body fidelity

### Added
- `naukainfo-author-body-fidelity` as the highest-priority skill.
- `audit_author_body_fidelity.py` and a 100% lexical / 99% structural fail-closed gate.
- `docs/SKILL_MAP.md` with execution order and pruning policy.

### Worked
- Source/final semantic signatures; allowed-change whitelist; manual-list preservation; repeated integrity checks.

### Did not work / removed from active logic
- Visual-similarity-only acceptance.
- Plain-text reconstruction of article bodies.
- Automatic conversion of all body lists.
- Unrequested grammar/style rewriting of scientific text.

## 1.9.0

- Added `naukainfo-annotation-keywords-normalization`: canonical bold labels, punctuation, language-aware casing, and authoritative Normal paragraph geometry.
- Added `naukainfo-author-header-cleanup`: email/phone/messenger removal without blank holes, ORCID preservation, role capitalization and `AUTOR`/`pip` verification.
- Added `naukainfo-reference-entry-reconstruction`: hand-typed numbering and Enter-split continuation repair, URL/DOI labels, ambiguity stop condition, and Ctrl+Space-equivalent rebuild.
- Upgraded `naukainfo-udc-review` with an online evidence packet, operator approval gate, insertion helper and exactly one blank after UDC.
- Made `Jurnal.dotx` the sole authoritative source of canonical style nodes; removed the failed visual-approximation `apply_canonical_article_styles.py` path and the incorrect zero-indent rule for annotation/keywords.
- Added two contact-bearing project-derived DOCX fixtures and new regression tests.
- Rebuilt and visually verified the two-article conference 136 journal; both reference lists independently restart at 1.

## 1.8.0

- Added `naukainfo-multi-article-assembly` for semantic extraction and composition of multiple validated articles into one ETALON journal.
- Added a hard per-article reference-numbering gate: every article receives a distinct `numId` with `startOverride=1`; continuation from a previous article is a build failure.
- Added the two-pass TOC workflow: stabilize pagination first, then insert actual internal start pages and re-render.
- Added trailing-section cleanup to prevent blank pages caused by appended article `sectPr` artifacts.
- Added exact article text/table sequence comparison and media/SmartArt preservation checks after merge.
- Added `scripts/multi_article_reference_restart.py`, dependency `docxcompose>=1.4`, and a regression test for two independent reference blocks.
- Verified a two-article draft journal: 19 physical pages, 3 tables, 5 article visuals, references 4+24, both lists starting at 1, no text loss and no final blank page.

## 1.7.0

- Added `naukainfo-spacing-toc-contract` for required blank paragraphs after article titles, figure/table/source blocks, and before/after the canonical reference stamp.
- Corrected reference-block contract: after `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` there must be one empty paragraph before the first source.
- Added TOC/outline gate: only `SECTION`, `AUTOR`, and `Назва1` may have outline levels; `pip` and all service/body styles must be excluded from generated TOC logic.
- Added Ctrl+Space-equivalent cleanup of reference runs to remove copied character overrides, hyperlink styles, underline/color, shadows and foreign substyles before applying `REFER`.
- Replaced failed acceptance logic: visual similarity without structural styleId/outline audit is no longer sufficient.
- Added deterministic `scripts/enforce_spacing_toc_references.py` and spacing/TOC regression tests.

## 1.6.0

- Added `naukainfo-table-figure-caption-contract` with verified table-number/title, `TABLETEXT`, `РИС`, `РисПід` and source-note rules.
- Added `naukainfo-reference-block-fidelity` with the canonical `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` stamp, exact blank spacing and per-article numbering restart.
- Fixed the regression where `REFER` paragraphs retained copied direct indentation/tabs and foreign `numId`, causing bullets/arrows and incorrect hanging alignment.
- Added deterministic `scripts/normalize_captions_references.py` plus caption/reference regression tests.
- Reprocessed the Hnysiuk article (1 table, 1 editable SmartArt, 4 references) and the Soloviov–Halenko–Debretseni article (2 tables, 4 figures, 24 references), with full render QA.
- Updated business rules, journal contract, integration plan, architecture, agent instructions and README.

## 1.5.0

- Added `naukainfo-canonical-style-application`.
- Made English-only section headings mandatory, resolved from the official section library and inserted once before the first article of each non-empty section.
- Made actual ETALON style IDs mandatory for section, DOI/UDC, author names, author metadata, title, drawing paragraphs, figure captions, table cells, reference heading and reference entries.
- Added deterministic `scripts/apply_canonical_article_styles.py` and regression test.
- Verified conference 136 Hnysiuk article as section 1: `ECONOMIC THEORY, MACRO- AND REGIONAL ECONOMY`.
- Corrected the Hnysiuk ETALON copy and removed the obsolete table page break after rendered A/B review.

## 1.4.0

- Added `naukainfo-semantic-style-routing` with a canonical paragraph-role/style map.
- Added a hard no-positive-first-line-indent rule for DOI/UDC, author metadata, titles, annotations, keywords, drawing paragraphs, figure/table captions, source notes, table cells, list items, reference headings and reference entries.
- Preserved intentional hanging indents and numbering geometry in references/lists.
- Added deterministic `scripts/semantic_paragraph_roles.py` and regression tests.
- Added `naukainfo-shape-object-fidelity` for SmartArt, grouped shapes, text boxes, DrawingML/VML and diagram relationship parts.
- Added deterministic shape normalization/audit scripts and a textbox regression test.
- Verified SmartArt transfer on the Hnysiuk motivation article and semantic-indent repair on both Hnysiuk and Soloviov–Halenko–Debretseni ETALON copies.
- Made verified skill/business-rule/documentation/test updates an automatic project obligation, without requiring the user to repeat the reminder.


## 1.3.0

- Added `naukainfo-table-format-fidelity` to prevent template style inheritance from changing table text placement.
- Added effective first-line indent resolution through direct paragraph properties, paragraph style, base-style chain, and defaults.
- Added deterministic `scripts/table_format_fidelity.py` and regression tests.
- Added the rule to use a direct zero override in table cells instead of changing the global ETALON `Normal` style.
- Expanded the journal contract, integration/business plan, architecture, ready-solutions register, and business-rules documentation.
- Verified the rule on the Soloviov–Halenko–Debretseni article: 49 inherited table indents corrected, zero remaining table paragraph/run differences after save/re-open.

## 1.2.0

- Added `naukainfo-pagination-break-reflow` for rendered A/B evaluation of author-inserted manual page breaks after 14→11 pt normalization.
- Added the publication-layout rule: remove an obsolete table-related break only when the table fits whole or splits no rougher than approximately 60/40 by rendered table volume.
- Added safeguards for captions, header rows, merged cells, notes, structural breaks, article-start breaks, and ambiguous cases.
- Added a hard agent-governance rule: “додай до скілів” requires an actual package update, tests/docs/changelog updates, and a new archive.
- Updated `naukainfo-minimal-normalization` and the journal contract to invoke the new pagination reflow review.

## 1.1.0

- Added `naukainfo-manifest-evidence-matching`: exact Excel↔DOCX audit using author name and article title as independent primary signals.
- Added `naukainfo-etalon-slot-insertion`: structural insertion after TABLE OF CONTENTS and before the protected tail section.
- Added deterministic `scripts/insert_article_into_etalon.py`.
- Documented verified object-preserving template insertion and required render audit.

## 1.0.0

- Added 11 portable NAUKAINFO Agent Skills.
- Added safe MCP adapter around the current Journal Builder CLI.
- Added explicit Agent Decision Bundle schema.
- Added read-only scan, inspection, test and rendering tools.
- Added build approval and path-isolation safeguards.
- Added integration plan for removing nested LLM decisions from the pipeline.

## v2.1
- Added `naukainfo-skill-map-change-log`.
- Updated author body fidelity: body lists remain author-original; only references are canonicalized.
- Updated multi-article assembly: static TOC is inserted first, rendered, page numbers corrected, then re-rendered.
- Documented the successful 6-article assembly pass and the discarded unsafe approach: changing body lists as if they were references.


## v2.2
- Added `naukainfo-toc-table-builder`: TOC must be a three-column Word table using `Tab_SEC`, `Tab_PIP`, `Tab_Taitl`, generated from `SECTION`/`AUTOR`/`Назва1` styles and final pagination.
- Added `naukainfo-front-matter-order-and-title-dedupe`: canonical DOI/UDC -> author header -> title order; exactly one blank before and after title; duplicate generated titles are forbidden.
- Fixed regression notes: loose paragraph TOC and manual `body_start_idx` title duplication are removed from active logic.
- Fixed page numbering preservation rule: the middle numbered section break from ETALON must be preserved before the final service page.

## v2.3 - PDF-accurate TOC geometry
- Upgraded `naukainfo-toc-table-builder` after PDF visual comparison.
- Fixed the v2.2 defect where article author/title/page were placed in one row and three equal columns.
- Added `scripts/rebuild_toc_pdf_contract.py`.
- New contract: merged section rows; per article two rows; number/content/page columns with fixed grid `[600, 8300, 739]` twips.
- Removed active logic that repeats section text in all three cells.


## v2.6 — scope guard + frontmatter/contact cleanup regression

- Strengthened project-scope boundary: these skills are only for the Дирежор / NAUKAINFO Journal Builder project and only after activation in the current chat.
- Fixed full-release regressions: author emails, damaged email remnants, author-supplied section notes, and comma-joined author/degree lines.
- Added anti-regression rule for canonical frontmatter order: DOI/UDC → header → title → annotation/abstract.
- Reconfirmed: author body after annotation must remain untouched except explicitly allowed NAUKAINFO normalization.


## v2.7
- Added `naukainfo-numbering-definition-fidelity`.
- Fixed regression where Hnysiuk body bullet list became decimal `1.`/`2.` after merge due to numbering.xml `numId` collision.
- Added rule: author body list markers are protected author structure; only references may be rebuilt as decimal restart lists.


## v2.8 — Critical fidelity hotfixes

Status: full release v2.6/v2.8 is not considered publishable until the new gates pass on all 24 source articles.

Added skills:
- `naukainfo-media-object-fidelity-gate` — blocks lost figures/drawings/media and caption detachment.
- `naukainfo-shape-textbox-nested-table-contract` — recursively inspects shapes/textboxes and nested tables/captions.
- `naukainfo-author-heading-emphasis-fidelity` — preserves author bold/italic/centered body subheadings.
- `naukainfo-frontmatter-supervisor-and-pip-split` — splits supervisors/people vs degrees/roles correctly.
- `naukainfo-table-caption-split-contract` — converts one-line table captions to canonical two-line format.
- `naukainfo-pagebreak-and-empty-paragraph-policy` — removes author page breaks and stray blanks while preserving required business blanks.
- `naukainfo-reference-language-and-marker-contract` — Ukrainian `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` vs English `REFERENCES`.

Regressions documented:
- Hnysiuk body list numbering changed due to numbering.xml collision.
- Magdysiuk Figure 2 was lost because media relationship fidelity was not deep enough.
- Magdysiuk body subheading bold was lost.
- Matviienko nested shape/table/caption content was not inspected recursively.
- Header classifier assigned `AUTOR` to degree/title lines in some cases.
- English reference blocks could receive the Ukrainian stamp.

Removed from active logic:
- text-only “content integrity” as a sufficient proof of journal safety;
- object-count-only checks without relationship/media/order validation;
- flat body scanning that ignores `w:txbxContent` and nested tables;
- generic replacement of all reference stamps with the Ukrainian heading.

## v2.9

- Preserved v2.8 and all earlier versioned backups; created a new clean package instead of overwriting.
- Migrated seven loose v2.8 skill files into canonical `skills/<name>/SKILL.md` directories.
- Added legacy binary DOC image recovery after the Novak regression exposed converter-omitted figures 1 and 4.
- Added atomic figure-cluster fidelity and SHA-256/relationship auditing.
- Added multilingual marker library, including German `Abb.`, `Literaturverzeichnis`, and `Quellenverzeichnis`.
- Added unnumbered table-label recognition after the Slabky article used standalone `Таблиця`.
- Added final TOC/body author synchronization after stale TOC content omitted Papinko and leaked `Hon. PhD`.
- Normalized English `REFERENCES`, numbered Ukrainian reference headings, and restored author bold emphasis for `13. Висновки`.
- Verified the repaired 24-article release on 99 rendered pages.

## 3.0.0 — 2026-07-11

### Added
- `naukainfo-etalon-section-pagination-fidelity`.
- `naukainfo-body-leading-space-normalization`.
- `naukainfo-free-listener-toc-section`.
- Verified v32 deterministic finalizer and release report.

### Changed
- Exact annotation→keywords→blank spacing.
- Article boundaries use `pageBreakBefore`, not dummy break paragraphs.
- Per-article media gate includes Todorova/Magdysiuk regression fixtures.
- Nested shape/textbox/table caption styling is recursively asserted.
- Reference block can be inferred at article end only with strong evidence.
- TOC includes the final manifest-driven `FREE LISTENERS` section.

### Worked
- Three ETALON sections and page-number footer survived assembly.
- 24 article starts, 6 listener records, and 96 rendered pages verified.

### Removed from active logic
- Aggregate object counts as sufficient fidelity proof.
- Break-only paragraphs between articles.
- Global whitespace cleanup.
- Marker-only bibliography detection.
