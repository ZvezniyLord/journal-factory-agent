# ASTRA_MASTER.md
## Codex 6 Astra — NAukaInfo Journal Factory

### 0. Mission
Build a clean-room, deterministic conference-journal factory inside the current workspace only.

The system must create a finished Word journal from:
- Excel participant registry;
- article/thesis DOCX/DOC files and questionnaires/applications;
- local journal template/etalon;
- section configuration;
- optional explicitly supplied old journals/articles used only as evidence/comparison.

The system must preserve scientific content and author-local formatting while applying NAukaInfo editorial rules.

### 1. Clean-room boundary — release-blocking
Treat the current Astra workspace as a new project.

MUST:
- create all code, tests, configs, caches, logs and outputs inside the current workspace;
- implement `path_guard`;
- reject `../`, parent scans, sibling-project scans and implicit discovery outside workspace;
- allow external data only when explicitly supplied by CLI/config and allowlisted;
- never inspect/import/copy old project code, `PROJECT_MAP`, parent/sibling scripts or previous implementation decisions;
- test the boundary automatically.

Old documents explicitly supplied as input are allowed as data. Old code is forbidden.

### 2. Sources of truth by domain
Do NOT use one global precedence chain for every field.

#### Semantic article content
1. explicit user/run correction
2. current original article
3. audit issue if unresolved

#### Local author formatting
1. explicit user/run correction
2. current original article
3. audit issue if unresolved

#### Participant / registration / services
1. explicit user/run correction
2. Excel registry
3. questionnaire/application
4. audit issue if unresolved

#### Global editorial formatting
1. explicit run override
2. `naukainfo.yaml`
3. journal template fallback

#### Front matter
- template-owned and immutable before `TABLE OF CONTENTS`;
- ordinary build rules may never override it.

#### Comparison evidence
- explicitly supplied old journals/articles only.

#### Hermes
- advisory evidence only;
- never authoritative for mutation.

### 3. Main architecture rule
Hermes interprets. Astra decides and mutates.

Astra owns deterministic parsing, manifests, matching thresholds, OOXML merge, styles, numbering, `REFER`, TOC, DOI/UDC application, QA, Word COM finalization and final verdicts.

Hermes may assist only with semantic ambiguity.

### 4. Context discipline
Do not keep whole archives, complete journals, huge XML parts, or hundreds of full articles in active model context.

Use:
`SPEC/config -> manifest -> Hermes JSON -> deterministic code -> QA JSON`

Persist stage state to disk. For every stage:
1. read only necessary inputs;
2. write structured output;
3. summarize stage in <=10 lines;
4. continue from disk state.

### 5. Required pipeline
1. boundary/path guard
2. input inventory + hashes
3. Excel parsing
4. DOC/DOCX extraction
5. article/questionnaire role detection
6. Hermes semantic scan where useful
7. deterministic article ↔ registry matching
8. template/style inspection
9. single-article normalization
10. bibliography/reference engine
11. multi-article OOXML-aware merge
12. TOC build
13. structural QA
14. content-integrity QA
15. formatting-integrity QA
16. object-integrity QA
17. Word COM finalization where available
18. render/visual QA
19. final release verdict

### 6. Required run artifacts
Each run must be isolated:

```text
runs/<run_id>/
  resolved_config.yaml
  input_manifest.json
  inventory.json
  source_index.json
  matches.json
  ambiguities.md
  metadata.json
  hermes/
    requests/
    responses/
    cache/
  extracted/
  normalized_articles/
  draft.docx
  journal.docx
  qa/
    structural.json
    content_integrity.json
    formatting_integrity.json
    object_integrity.json
    bibliography.json
    toc.json
    front_matter.json
    report.md
  render/
```

Never overwrite source files.

### 7. Blocking golden tests BEFORE full builder
Do not build the full production pipeline until these pass:

1. path guard denies parent/sibling code access;
2. explicit allowlisted external input is permitted;
3. two articles with two bibliographies both start at `1`;
4. `REFER` is a real Word list binding, not just a visible style label;
5. institution is never parsed as an author;
6. scientific supervisor appears in TOC for NAukaInfo profile;
7. front matter before `TABLE OF CONTENTS` is unchanged;
8. bold, italic, underline, subscript and superscript survive normalization;
9. table, image and hyperlinks survive merge;
10. `Normal` is not globally mutated to normalize article body;
11. Hermes timeout/500/invalid JSON cannot corrupt deterministic pipeline;
12. duplicate article insertion is blocked;
13. missing object/text causes BLOCKED, not PASS.

### 8. Word/OOXML rules
DOCX is a ZIP package of related XML parts.

Use high-level libraries where safe, but low-level OOXML is allowed/required for numbering, styles, relationships, section properties, drawings/media, embedded objects, hyperlinks, OMML and complex merges.

Do not flatten DOCX to plain text/HTML and rebuild.
Do not globally rewrite `Normal`.

Do not mass-delete `keepNext`, `keepLines`, widow/orphan controls, page breaks, section breaks, fields, bookmarks or hidden text.

### 9. Release statuses
Only:
- `PASS`
- `PASS_WITH_WARNINGS`
- `BLOCKED`

`PASS` is forbidden if any required invariant is unresolved.

Blocking examples:
- unmatched required article;
- semantic text loss;
- table/image/formula loss;
- corrupt DOCX;
- bibliography carry-over;
- wrong TOC article count/order;
- institution parsed as author;
- supervisor omitted from TOC under NAukaInfo profile;
- front matter changed;
- duplicate article insertion;
- unexplained bold/italic/subscript loss.

### 10. Definition of Done
A run is done only when:
- every Excel participant is accounted for;
- every intended material appears exactly once;
- free listeners are handled correctly;
- TOC matches final order;
- front matter is unchanged;
- article semantic text is preserved;
- author-local formatting is preserved except explicit editorial overrides;
- tables/images/equations/hyperlinks survive;
- every bibliography is structurally correct and restarts at 1;
- journal opens in Microsoft Word;
- Word/render QA passes;
- reports explain every warning/difference;
- final `journal.docx` physically exists.

### 11. Implementation order
Implement and test in this order:
1. path guard + run model
2. typed schemas
3. inventory + archive safety
4. Excel parser
5. DOCX inspector/extractor
6. DOC conversion adapter
7. Hermes adapter
8. deterministic matcher
9. template/style reader
10. article normalization
11. reference engine
12. merge engine
13. TOC
14. integrity validators
15. Word COM adapter
16. visual QA
17. CLI
18. full end-to-end run

### 12. Final instruction
Read `EDITORIAL_RULES.md`, `HERMES_PROTOCOL.md` and `naukainfo.yaml`.
Convert their rules into code, schemas, config validation and tests.
Do not repeatedly re-ingest large documents into model context.
Do not claim completion until an actual journal build and QA have completed.
