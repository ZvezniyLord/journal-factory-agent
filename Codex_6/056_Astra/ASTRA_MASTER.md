# ASTRA_MASTER.md
## Codex 6 Astra — NAukaInfo Journal Factory

### 0. Mission
Build a clean-room, deterministic conference-journal factory inside this workspace only.

Inputs may include:
- Excel participant registry;
- article/thesis DOCX/DOC files;
- questionnaires/applications;
- local journal template/etalon;
- section configuration;
- explicitly supplied old journals/articles as comparison evidence only.

The system must preserve scientific content and meaningful author-local formatting while applying NAukaInfo editorial rules.

## 1. Mandatory Phase 0 — connect Hermes before planning
Hermes is not an optional late-stage feature. It is the local semantic subagent used to reduce Astra context/token load.

Before writing the architecture plan or production code:

1. Read `config/hermes_runtime.json`.
2. Try the configured **main** OpenAI-compatible endpoint.
3. Verify model discovery.
4. Send the configured strict-JSON bootstrap smoke prompt.
5. Save the real handshake result to `runs/bootstrap/hermes_handshake.json`.
6. If main fails, try the configured fallback worker.
7. If both fail, stop with `BLOCKED_HERMES_BOOTSTRAP`; do not silently continue as if Hermes were available.
8. After a successful handshake, draft a compact implementation plan.
9. Send only that compact plan + constraints to Hermes using task `review_astra_plan`.
10. Save Hermes review to `runs/bootstrap/hermes_plan_review.json`.
11. Astra decides which suggestions to adopt and records that in `ARCHITECTURE.md` / `IMPLEMENTATION_PLAN.md`.

During the rest of development and journal runs, use Hermes as a bounded semantic subagent. Do not make Astra itself read hundreds of full documents when a compact extraction can be delegated.

Core rule:

> **Hermes interprets; Astra decides and mutates.**

## 2. Clean-room boundary — release-blocking
Treat this workspace as a new project.

MUST:
- create all code, tests, configs, caches, logs and outputs inside this workspace;
- implement `path_guard`;
- reject `../`, parent scans, sibling-project scans and implicit discovery outside workspace;
- allow external data only when explicitly supplied and allowlisted;
- never inspect/import/copy old project code, `PROJECT_MAP`, parent/sibling scripts or previous implementation decisions;
- test the boundary automatically.

Explicitly supplied old documents are allowed as **data/evidence**. Old code is forbidden.

The local Hermes endpoint in `config/hermes_runtime.json` is runtime infrastructure, not legacy project code.

## 3. Sources of truth by domain

### Semantic article content
1. explicit user/run correction
2. current original article
3. audit issue if unresolved

### Local author formatting
1. explicit user/run correction
2. current original article
3. audit issue if unresolved

### Participant / registration / services
1. explicit user/run correction
2. Excel registry
3. questionnaire/application
4. audit issue if unresolved

### Global editorial formatting
1. explicit run override
2. `naukainfo.yaml`
3. journal template fallback

### Front matter
- template-owned and immutable before `TABLE OF CONTENTS`;
- ordinary build rules may never override it.

### Comparison evidence
- explicitly supplied old journals/articles only.

### Hermes
- advisory evidence only;
- never authoritative for DOCX mutation or release verdict.

## 4. Skill integration decisions
Read `SKILL_INTEGRATION.md`.

Accepted capabilities are consolidated into code/tests rather than implemented as ten unrelated agents.

Existing NAukaInfo UDC and spelling/header capabilities remain authoritative. The people-role capability only supplements them with role separation and supervisor-in-TOC rules.

## 5. Context discipline
Do not keep whole archives, complete journals, huge XML parts or hundreds of full articles in active Astra context.

Preferred flow:

`SPEC/config -> deterministic extraction -> compact Hermes task -> validated JSON -> manifest -> deterministic mutation -> QA JSON`

For every stage:
1. read only necessary inputs;
2. write structured output to disk;
3. summarize stage in <=10 lines;
4. continue from compact state files.

Raw Hermes responses belong on disk, not in Astra's continuing reasoning context.

## 6. Required pipeline
0. Hermes bootstrap + plan review
1. boundary/path guard
2. input inventory + hashes
3. Excel parsing
4. DOC/DOCX extraction
5. article/questionnaire role detection
6. Hermes semantic scan for noisy/ambiguous material
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

## 7. Required run artifacts
Each run is isolated:

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

Bootstrap artifacts:

```text
runs/bootstrap/
  hermes_handshake.json
  hermes_plan_review.json
```

Never overwrite source files.

## 8. Blocking golden tests BEFORE full builder
Do not build the full production pipeline until these pass:

1. path guard denies parent/sibling code access;
2. explicit allowlisted external input is permitted;
3. real Hermes bootstrap can be validated when configured runtime is available;
4. two articles with two bibliographies both start at `1`;
5. `REFER` is a real Word list binding, not just a visible style label;
6. institution is never parsed as an author;
7. scientific supervisor appears in TOC for NAukaInfo profile;
8. front matter before `TABLE OF CONTENTS` is unchanged;
9. bold, italic, underline, subscript and superscript survive normalization;
10. table, image and hyperlinks survive merge;
11. `Normal` is not globally mutated;
12. Hermes timeout/500/invalid JSON cannot corrupt deterministic pipeline;
13. duplicate article insertion is blocked;
14. missing object/text causes BLOCKED, not PASS;
15. canonical body styles have no autoRedefine/theme-font dependency;
16. save-close-reopen Word roundtrip does not change effective formatting/layout.

## 9. Word/OOXML rules
DOCX is a ZIP package of related XML parts.

Use high-level libraries where safe, but low-level OOXML is allowed/required for:
- numbering;
- styles;
- relationships;
- section properties;
- drawings/media;
- embedded objects;
- hyperlinks;
- OMML;
- complex merges.

Do not flatten DOCX to plain text/HTML and rebuild.
Do not globally rewrite `Normal`.

Do not mass-delete `keepNext`, `keepLines`, widow/orphan controls, page breaks, section breaks, fields, bookmarks or hidden text.

## 10. Release statuses
Only:
- `PASS`
- `PASS_WITH_WARNINGS`
- `BLOCKED`

`PASS` is forbidden if any required invariant is unresolved.

Blocking examples:
- Hermes required bootstrap unavailable for the configured development run;
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

## 11. Definition of Done
A run is done only when:
- every Excel participant is accounted for;
- every intended material appears exactly once;
- free listeners are handled correctly;
- TOC matches final order;
- front matter is unchanged;
- semantic text is preserved;
- meaningful author-local formatting is preserved except explicit editorial overrides;
- tables/images/equations/hyperlinks survive;
- every bibliography is structurally correct and restarts at 1;
- journal opens in Microsoft Word;
- Word/render QA passes;
- reports explain every warning/difference;
- final `journal.docx` physically exists.

## 12. Implementation order
1. Hermes real bootstrap + smoke test
2. compact plan + Hermes plan critique
3. path guard + run model
4. typed schemas
5. inventory + archive safety
6. Excel parser
7. DOCX inspector/extractor
8. DOC conversion adapter
9. production Hermes adapter + cache
10. deterministic matcher
11. template/style reader
12. article normalization
13. reference engine
14. merge engine
15. TOC
16. integrity validators
17. Word COM adapter
18. Word reopen/style-stability validator
19. visual QA
20. CLI
21. full end-to-end run

## 13. Final instruction
Read:
1. `EDITORIAL_RULES.md`
2. `HERMES_PROTOCOL.md`
3. `SKILL_INTEGRATION.md`
4. `naukainfo.yaml`
5. `config/hermes_runtime.json`

Convert rules into code, schemas, config validation and tests.
Use Hermes early and continuously for bounded semantic work.
Do not repeatedly re-ingest large documents into Astra context.
Do not claim completion until an actual journal build and QA have completed.
