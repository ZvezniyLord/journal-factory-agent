# Journal Factory — Business Logic and Development Roadmap

## 1. Product goal

Journal Factory is a local browser-driven system for preparing a complete scientific journal or conference proceedings issue from a mixed folder of source files.

The system must:

1. accept a source folder and journal number from a human operator;
2. create a controlled workspace;
3. discover Excel registries, article files, templates, images, archives, and supporting materials;
4. match registry records to article documents even when names and titles use different languages or transliterations;
5. process every article independently;
6. recognize the document structure using deterministic rules, repeated visual markers, registry evidence, retrieval evidence, and a local LLM only for unresolved ambiguity;
7. normalize and transform each article;
8. assemble the journal in the correct order;
9. render DOCX to PDF and PNG;
10. verify structural and visual quality;
11. produce complete reports and an auditable decision history.

The final system must run locally, preserve source files, never silently guess, and never present an unverified draft as a finished journal.

---

## 2. Non-negotiable universal document rule

After the dashboard and workspace have been created, the first document-editing operation is universal text normalization.

Every editable text element must use:

- font size: **11 pt**;
- line spacing: **1.0 / single**.

This rule applies to all editable text, including:

- article body;
- article header;
- authors;
- affiliations;
- scientific degrees and positions;
- UDC;
- article titles;
- annotations and abstracts;
- keywords;
- all headings;
- table cells;
- table captions;
- figure captions;
- editable labels associated with figures;
- references and bibliography entries;
- headers and footers;
- page service text;
- notes and other editable objects.

Text rasterized inside an image cannot be reformatted. The image caption and every editable text object around it must still follow 11 pt and 1.0.

Any editable production text that violates 11 pt or 1.0 is a hard `FAIL`.

---

## 3. Single operator entry point

The only human-facing entry point is root `index.html`, served by a local backend on `127.0.0.1`.

The human must not operate the system from the command line during normal use.

The first screen contains:

- journal/conference number;
- source folder path;
- source-folder chooser;
- output-parent path;
- output-folder chooser;
- default output location on the current user's Desktop;
- calculated workspace root;
- validation state;
- button to create the workspace and start the run.

Default output path:

```text
<Desktop>/<journal_number>/
```

The interface must later evolve into an interactive game-like process map with:

- visual cores/nodes;
- active, completed, warning, and failed states;
- progress for the complete run;
- article-by-article cards;
- detected marker cards;
- author-match explanations;
- confidence scores;
- local LLM call history;
- operator decisions;
- report links;
- final quality gate.

The browser contains presentation and interaction only. Business rules remain in backend cores.

---

## 4. Architectural law

The system must follow:

- OOP;
- SOLID;
- dependency inversion;
- ports and adapters;
- immutable domain models where practical;
- typed errors;
- explicit interfaces;
- deterministic core logic;
- isolated local LLM calls;
- test-first development.

Forbidden:

- one monolithic script;
- a single class that owns unrelated responsibilities;
- filesystem operations in domain models;
- HTTP logic in document cores;
- business logic in HTML;
- ad-hoc absolute paths;
- silent fallback;
- unlogged LLM decisions;
- hidden mutation of source files;
- treating a generated DOCX as final without the quality gate.

Every core must expose an interface and produce machine-readable reports.

---

## 5. Canonical workflow

The high-level business process is:

```text
Operator input
  -> Workspace creation
  -> Dashboard activation
  -> Source discovery
  -> Immutable source snapshot
  -> Registry detection and parsing
  -> Article discovery
  -> Working-folder creation
  -> Raw article copies
  -> Article-to-registry matching
  -> Per-article segmentation
  -> Universal 11 pt / 1.0 normalization
  -> Header parsing and normalization
  -> Marker and structure resolution
  -> Table/figure/reference handling
  -> Transformed article output
  -> Per-article QA
  -> Journal assembly in registry order
  -> TOC/front matter/pagination
  -> DOCX output
  -> PDF and PNG rendering
  -> Structural and visual QA
  -> Final PASS / PASS WITH WARNINGS / FAIL
```

The dashboard is created before document work and remains active throughout the run.

---

## 6. Workspace business rules

### 6.1 Source safety

The source folder is read-only from the business-process perspective.

The system must never edit source documents in place.

Before transformation, it creates an immutable source snapshot and records hashes.

### 6.2 Required workspace tree

```text
<output_parent>/<journal_number>/
├── source_snapshot/
├── articles_raw/
├── articles_transformed/
├── reports/
├── logs/
├── database/
├── rendered/
│   ├── pdf/
│   └── png/
├── final/
└── temp/
```

### 6.3 Separate original and transformed articles

`articles_raw/` contains copied original article files.

`articles_transformed/` contains transformed article outputs.

One source article maps to one independently processed transformed article.

### 6.4 Path authority

All cores receive paths from `PathRegistry` through `WorkspaceDriverPort`.

No other core may construct arbitrary absolute paths.

### 6.5 Required workspace reports

At minimum:

- `reports/run_manifest.json`;
- `reports/path_registry.json`;
- `reports/report_registry.json`;
- `reports/action_log.jsonl`;
- `reports/run_summary.html`.

Every material action is appended to the action log.

---

## 7. Core map

## 7.1 Workspace Driver Core

Primary class: `WorkspaceDriver`.

Responsibilities:

- validate workspace input;
- resolve Desktop default;
- normalize paths;
- create the canonical workspace;
- create `RunContext`;
- remember every path;
- register reports;
- append actions;
- expose state to the UI;
- support resume/reconstruction from persisted reports.

It must not parse Excel, DOCX, article semantics, or invoke an LLM.

Required abstractions:

- `WorkspaceConfig`;
- `WorkspaceLayout`;
- `RunContext`;
- `ActionRecord`;
- `ReportRecord`;
- `PathRegistry`;
- `ReportRegistry`;
- `WorkspaceDriverPort`;
- `FileSystemAdapter`.

## 7.2 Browser UI Core

Responsibilities:

- serve root `index.html`;
- display defaults and validation;
- display the live pipeline map;
- reconstruct UI state from reports;
- show article status and errors;
- request operator confirmation for ambiguous cases;
- never implement document business logic.

## 7.3 Source Discovery Core

Responsibilities:

- recursively scan the selected source folder;
- detect Excel files;
- detect DOC/DOCX article files;
- detect templates;
- detect images;
- detect archives;
- detect duplicate and unsupported files;
- produce a deterministic source inventory;
- report ambiguity instead of guessing.

Required reports:

- archive/source inventory;
- file classification;
- duplicates;
- unsupported files;
- discovery warnings.

## 7.4 Source Snapshot Core

Responsibilities:

- copy source assets into `source_snapshot/`;
- compute SHA-256;
- record source and destination paths;
- prove that the snapshot is unchanged later;
- never overwrite a different existing file silently.

## 7.5 Excel Registry Core

Responsibilities:

- identify the correct workbook and sheet;
- read author names;
- read titles;
- read section/order data;
- read journal number and identifiers;
- normalize whitespace, punctuation, and case;
- preserve original values alongside normalized values;
- produce typed registry records;
- report missing or conflicting fields.

No matching decision is made inside the Excel parser itself.

## 7.6 Retrieval and Matching Core

Purpose: match Excel records to article files across language and transliteration differences.

Examples:

- English surname in Excel, Ukrainian surname in the article;
- different transliteration standards;
- initials in one source, full names in another;
- title wording differences;
- different punctuation or order of authors.

Matching stages:

1. exact normalized comparison;
2. punctuation and whitespace normalization;
3. case folding;
4. Unicode normalization;
5. transliteration variants;
6. surname/initial token comparison;
7. title token similarity;
8. co-author evidence;
9. affiliation evidence;
10. local retrieval database evidence;
11. local LLM arbitration only when ambiguity remains.

The retrieval layer may be called RAG, RA, or a local retrieval index, but its responsibilities are fixed:

- store normalized registry records;
- store article metadata candidates;
- store transliteration aliases;
- retrieve likely matches quickly;
- return weighted evidence;
- return confidence scores;
- explain why a match was proposed.

Required matching output:

- chosen registry record or unresolved status;
- candidate list;
- score per candidate;
- evidence weights;
- deterministic/LLM decision source;
- confidence;
- warning or blocking status.

No low-confidence match may be silently accepted.

## 7.7 Article Processing Coordinator

Processes articles one by one.

Each article must be handled independently so the complete article or selected sections fit the local LLM context.

The coordinator:

- receives a matched article record;
- creates an article-specific work context;
- calls segmentation, normalization, Header Core, object handling, and QA through interfaces;
- persists intermediate results;
- can resume one article without rebuilding all others;
- never merges all article logic into one function.

## 7.8 Marker Knowledge Core

Purpose: identify repeated structure markers across articles and journals.

Core markers include multilingual variants of:

- УДК / UDC;
- анотація / annotation / abstract;
- ключові слова / keywords / key words;
- таблиця / table;
- рисунок / рис. / figure / fig.;
- references;
- bibliography;
- список використаних джерел;
- література;
- other recurring heading-like labels.

The core must learn or register markers from the provided corpus while preserving deterministic review.

Evidence may include:

- text value;
- language;
- paragraph position;
- font attributes;
- bold/italic/all-caps;
- alignment;
- spacing before/after;
- proximity to tables or images;
- recurrence across authors;
- registry evidence.

The LLM may suggest marker classification, but the final result is logged and validated.

## 7.9 Article Segmentation Core

Responsibilities:

- split a DOCX into logical blocks;
- identify header boundary;
- body sections;
- annotations;
- keywords;
- tables;
- figures;
- captions;
- reference section;
- unknown blocks;
- preserve original ordering and object relationships.

It must not destroy unsupported content. Unknown blocks are preserved and reported.

## 7.10 Header Core

This is a separate, high-complexity kernel.

“Header” means the article front block before the main body and may include:

- UDC;
- author names;
- initials;
- scientific degrees;
- academic titles;
- positions;
- department/institution;
- city and country;
- ORCID or other identifiers;
- article title;
- language variants;
- correspondence data;
- boundaries between header and article body.

The Header Core combines:

1. deterministic text markers;
2. position in the article;
3. style and visual evidence;
4. Excel registry evidence;
5. matching/retrieval evidence;
6. repeated patterns learned from journal samples;
7. local LLM arbitration only for unresolved ambiguity.

It must output:

- structured header model;
- source paragraph/object references;
- normalized values;
- unresolved fields;
- confidence per field;
- complete decision explanation;
- transformed header block.

Header parsing and header rendering must be separate responsibilities.

## 7.11 Document Normalization Core

The first transformation applied to each article.

Responsibilities:

- apply 11 pt to every editable text run;
- apply single spacing 1.0 to every paragraph;
- handle paragraphs in table cells;
- handle headers and footers;
- handle captions;
- handle text boxes or supported drawing text where technically accessible;
- preserve images and non-text objects;
- verify the written DOCX after saving;
- report every uneditable or unsupported text object.

The core must inspect the saved document, not assume that style assignment worked.

## 7.12 Table Core

Responsibilities:

- detect and preserve tables;
- normalize editable table text to 11 pt / 1.0;
- preserve merged cells;
- preserve row and column relationships;
- detect captions;
- keep captions associated with tables;
- report oversized or broken tables;
- support deterministic width/layout rules later.

## 7.13 Figure Core

Responsibilities:

- preserve images and drawings;
- identify figure captions;
- maintain image/caption relationship;
- normalize editable caption text;
- detect missing captions or references;
- preserve source image quality;
- report inaccessible embedded objects.

## 7.14 Reference Core

Responsibilities:

- locate reference section using multilingual markers;
- preserve entries;
- normalize editable text;
- later support numbering and in-text citation consistency;
- detect duplicate or missing numbering;
- report uncertain section boundaries.

## 7.15 Article QA Core

Runs after each transformed article.

Checks:

- 11 pt everywhere editable;
- single spacing everywhere;
- header structure;
- required markers;
- tables and figures preserved;
- references preserved;
- no source content unexpectedly lost;
- no invalid relationships in DOCX;
- article opens successfully;
- visual render available where required.

Output:

- per-article PASS / PASS WITH WARNINGS / FAIL;
- structured findings;
- artifact paths;
- before/after comparison.

## 7.16 Assembly Core

Responsibilities:

- order articles according to Excel registry;
- insert front matter;
- create sections;
- combine transformed articles;
- preserve tables, figures, styles, relationships, and references;
- generate TOC;
- manage section/page breaks;
- manage pagination;
- produce final DOCX draft;
- never use source articles directly when transformed approved copies exist.

## 7.17 Rendering Core

Responsibilities:

- render final DOCX to PDF;
- render PDF pages to PNG;
- record renderer/version;
- preserve page count;
- detect conversion failure;
- provide artifacts for visual QA.

## 7.18 Final QA Core

Checks:

- every expected article exists in final output;
- article order matches registry;
- titles/authors match accepted records;
- TOC links and page numbers are valid where supported;
- 11 pt / 1.0 invariant holds;
- tables and figures are present;
- no unexpected blank pages;
- no clipped or overlapping content;
- pagination is coherent;
- PDF/PNG render matches DOCX structure;
- all unresolved warnings are visible.

Final statuses:

- `PASS` — production-ready;
- `PASS WITH WARNINGS` — usable only with explicit operator awareness;
- `FAIL` — not production-ready.

The system may not label output final unless the final quality report explicitly marks it production-ready.

---

## 8. Local LLM policy

The local LLM is not the primary executor of deterministic document operations.

Use deterministic Python/XML logic for:

- filesystem operations;
- hashing;
- DOCX/XML modification;
- font and spacing rules;
- object copying;
- registry parsing;
- report generation;
- merge/assembly;
- validation;
- tests.

Use the local LLM only for ambiguity such as:

- multilingual author equivalence;
- uncertain transliteration;
- uncertain header boundary;
- uncertain marker classification;
- conflicting semantic evidence;
- explanation of a proposed match.

Every LLM call must record:

- call id;
- article id;
- purpose;
- input references or digest;
- model name/version;
- prompt version;
- output;
- confidence;
- validation result;
- final accepted/rejected decision;
- reason;
- timestamp and duration.

No LLM output directly mutates a document without deterministic validation.

---

## 9. Database and retrieval business logic

The local database must support fast lookup and reproducibility.

Recommended separation:

- relational metadata store for canonical records and audit data;
- retrieval/vector or token index for fuzzy multilingual search;
- alias/transliteration table;
- decision/evidence table;
- article-state table.

Minimum entities:

- journal run;
- registry record;
- author;
- author alias;
- article source;
- article metadata candidate;
- match candidate;
- match evidence;
- accepted match;
- marker;
- marker occurrence;
- LLM decision;
- report;
- artifact;
- QA finding.

A database decision must remain reproducible from stored inputs, weights, rules, and model metadata.

---

## 10. Audit and reporting rules

Every core emits reports and action events.

Every action event includes:

- timestamp;
- run id;
- core;
- article id when applicable;
- action;
- status;
- input references;
- output references;
- message;
- warning/error code;
- duration;
- deterministic or LLM source.

Required report categories:

- workspace;
- discovery;
- snapshot and hashes;
- registry parsing;
- matching;
- markers;
- header parsing;
- document normalization;
- object preservation;
- article QA;
- assembly;
- rendering;
- final QA;
- acceptance verification.

Reports must be machine-readable. Human HTML summaries may be generated from them.

---

## 11. Error policy

Errors must be typed and visible.

Examples:

- `SOURCE_PATH_NOT_FOUND`;
- `SOURCE_PATH_NOT_DIRECTORY`;
- `OUTPUT_PATH_NOT_WRITABLE`;
- `WORKSPACE_COLLISION`;
- `REGISTRY_NOT_FOUND`;
- `MULTIPLE_REGISTRIES_AMBIGUOUS`;
- `ARTICLE_UNMATCHED`;
- `ARTICLE_MATCH_LOW_CONFIDENCE`;
- `HEADER_BOUNDARY_UNRESOLVED`;
- `MARKER_UNRESOLVED`;
- `DOCX_CORRUPT`;
- `TEXT_NORMALIZATION_FAILED`;
- `TABLE_PRESERVATION_FAILED`;
- `FIGURE_PRESERVATION_FAILED`;
- `RENDER_FAILED`;
- `QUALITY_GATE_FAILED`.

The browser must never receive an unhandled Python traceback.

The operator must see a human-readable explanation and a stable error code.

---

## 12. Test strategy

Development is cyclic and test-first:

```text
PLAN
-> FAILING TEST
-> MINIMAL IMPLEMENTATION
-> FOCUSED TEST
-> FULL REGRESSION
-> ARTIFACT INSPECTION
-> ARCHITECTURE REVIEW
-> REPOSITORY ACCEPTANCE
-> FIX
-> REPEAT
```

Test categories:

- unit tests for pure models and rules;
- adapter tests for filesystem, DOCX/XML, database, and renderer;
- API tests;
- browser/UI tests;
- integration tests per core;
- golden-file tests for DOCX transformations;
- round-trip tests;
- visual regression tests using rendered pages;
- fault-injection tests;
- acceptance tests against complete synthetic fixtures.

Tests must not write to the real Desktop, call production LLM endpoints, or depend on user files.

---

## 13. Detailed staged roadmap

## Phase 0 — Verified clean bootstrap

Deliverables:

- only approved bootstrap files;
- complete `AGENTS.md`;
- repository acceptance skill;
- Codex instruction;
- this business-logic roadmap;
- verified local/remote equality;
- no old MVP residue.

Gate: `skills/repository_acceptance/SKILL.md` returns `PASS`.

## Phase 1 — Workspace Driver and start menu

Deliverables:

- root `index.html`;
- local server;
- Desktop default;
- source and output selection;
- workspace validation;
- complete canonical directory tree;
- path and report registries;
- action log;
- launcher;
- state endpoint;
- complete tests.

No document logic yet.

## Phase 2 — Source Discovery and Snapshot

Deliverables:

- recursive inventory;
- file classification;
- archive support plan and safe extraction;
- duplicate detection;
- SHA-256;
- immutable snapshot;
- discovery dashboard;
- tests for mixed and malformed source folders.

## Phase 3 — Excel Registry Core

Deliverables:

- workbook/sheet detection;
- canonical registry model;
- author/title/order extraction;
- original plus normalized values;
- conflict reports;
- Excel fixtures and tests.

## Phase 4 — Raw Article Collection

Deliverables:

- article candidate classification;
- copy into `articles_raw/`;
- stable article IDs;
- source provenance;
- duplicate handling;
- per-article work contexts.

## Phase 5 — Matching Database and Retrieval

Deliverables:

- local metadata database;
- author alias/transliteration storage;
- deterministic matching pipeline;
- weighted evidence;
- candidate ranking;
- confidence thresholds;
- unresolved queue;
- explainable matching reports;
- small local LLM arbitration contract;
- benchmark fixtures.

## Phase 6 — Marker Corpus and Segmentation

Deliverables:

- multilingual marker dictionary;
- corpus-derived repeated marker candidates;
- paragraph/object classifier;
- article block model;
- unknown-block preservation;
- segmentation reports;
- deterministic and LLM-assisted ambiguity tests.

## Phase 7 — Universal Document Normalization

Deliverables:

- 11 pt / 1.0 transformer;
- table/header/footer/caption coverage;
- saved-document verification;
- unsupported object report;
- golden DOCX tests;
- hard-failure gate.

This phase must precede stylistic specialization.

## Phase 8 — Header Core

Deliverables:

- structured header model;
- field extraction;
- header/body boundary detection;
- multilingual support;
- registry/retrieval integration;
- confidence per field;
- deterministic header renderer;
- extensive fixture corpus;
- ambiguity queue and operator review.

## Phase 9 — Tables, Figures, and References

Deliverables:

- independent Table Core;
- independent Figure Core;
- independent Reference Core;
- preservation and caption linking;
- required formatting enforcement;
- missing-object detection;
- per-object QA.

## Phase 10 — Complete Per-Article Transformation

Deliverables:

- coordinator combining approved cores;
- transformed article output;
- article manifest;
- resume/retry support;
- article QA;
- dashboard article cards;
- PASS/WARN/FAIL per article.

## Phase 11 — Assembly Core

Deliverables:

- Excel-order assembly;
- front matter;
- section structure;
- TOC;
- page/section breaks;
- pagination;
- final DOCX draft;
- provenance linking every final block to its article source.

## Phase 12 — Rendering

Deliverables:

- DOCX to PDF;
- PDF to PNG;
- renderer metadata;
- page-count validation;
- render failure handling;
- artifacts shown in the dashboard.

## Phase 13 — Final Structural and Visual QA

Deliverables:

- structure checks;
- content completeness checks;
- font/spacing invariant scan;
- table/figure checks;
- blank/clipped/overlap checks;
- TOC/order checks;
- final quality report;
- PASS / PASS WITH WARNINGS / FAIL.

## Phase 14 — Interactive production dashboard

Deliverables:

- game-like pipeline map;
- live progress;
- article drill-down;
- evidence and confidence views;
- LLM decision history;
- operator decision queue;
- report/artifact viewer;
- resume and retry controls;
- final release gate.

## Phase 15 — Packaging and deployment

Deliverables:

- one-button Windows launcher;
- dependency bootstrap;
- local-only network policy;
- versioned configuration;
- backups and migration policy;
- reproducible release package;
- user manual;
- recovery guide.

---

## 14. Phase transition law

A phase may start only after the previous phase has:

- all focused tests passing;
- full regression passing;
- generated artifacts inspected;
- architecture review passed;
- repository acceptance skill passed;
- local and remote states matched;
- exact deliverables recorded;
- no unexplained TODO, skip, xfail, stub, or legacy residue.

A commit title or Codex success message is never sufficient evidence.

---

## 15. Definition of production-ready output

The journal is production-ready only when:

- every expected registry record is accounted for;
- every accepted article match is explainable;
- all transformed articles pass article QA;
- the final order matches the registry;
- every editable text object is 11 pt and 1.0;
- tables, figures, captions, and references are preserved;
- final DOCX opens successfully;
- PDF and PNG rendering succeeds;
- final visual and structural checks pass;
- all warnings are resolved or explicitly accepted;
- the final quality report contains:

```json
{
  "production_ready": true
}
```

Without that explicit value, the output remains a draft.
