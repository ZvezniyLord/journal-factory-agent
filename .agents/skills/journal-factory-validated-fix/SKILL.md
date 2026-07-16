---
name: journal-factory-validated-fix
description: Fix and validate Journal Factory DOCX generation, semantic structure, canonical styles, business rules, TOC, local-LLM classification, release gates, and review publishing. Use for journal defects, conference runs, regression work, or repository consolidation that can affect production behavior.
---

# Journal Factory validated fix workflow

Follow this workflow in order. Do not skip evidence collection.

## 1. Establish scope

1. Read `AGENTS.md`.
2. Read:
   - `docs/REPOSITORY_CONSOLIDATION.md` when repository structure or migration is involved;
   - `docs/JOURNAL_FACTORY_FIX_PROTOCOL.md`;
   - `docs/LLM_FIX_EVAL_PROTOCOL.md` for semantic model work;
   - active acceptance criteria under `docs/runs/`, when present.
3. Record repository, branch, remotes, visibility, dirty files, source run, target run, and protected/private artifacts.
4. Do not modify code during initial inventory.

## 2. Classify the work

Assign one primary class to every defect or migration item.

### Deterministic

Examples:

- Word styles and style IDs;
- direct formatting;
- DOCX merge mappings;
- numbering IDs;
- images, formulas, tables, relationships, shapes, and textboxes;
- bookmarks, TOC rows, page numbers, and section properties;
- Word repair warnings;
- release gates;
- repository layout, dependency ownership, and duplicate code removal.

Required process:

1. reproduce with a deterministic fixture or repository inventory;
2. define the contract;
3. write or update a failing test or validator;
4. implement the smallest root-cause fix;
5. run focused checks, then the full suite;
6. inspect DOCX XML, rendered output, or repository diff as applicable.

Do not use an LLM to decide deterministic values.

### LLM-dependent

Examples:

- ambiguous title, author, affiliation, epigraph, abstract-heading, or DOI classification;
- translated-title matching;
- ambiguous semantic role proposals.

Required process:

1. create a minimal safe fixture;
2. run the current production prompt against the configured local model;
3. use stable settings and structured output;
4. run at least five repetitions for critical cases;
5. save requests, responses, parse results, latency, and pass/fail in a private workspace;
6. test candidate prompts outside tracked production code;
7. require 5/5 correct critical classifications;
8. re-run all previous benchmark cases;
9. change tracked code only after the candidate is proven;
10. re-run through the production code path;
11. use a deterministic rule or operator action when the model remains unstable.

Priority:

`validated manifest → deterministic structural rule → schema/position rule → local LLM → operator action`

An LLM must not override strong deterministic evidence.

### Operator-only

Examples:

- unresolved author identity;
- proposed UDC values requiring approval;
- conflicting source files;
- missing authoritative template or manifest;
- policy or publication decisions.

Record an explicit operator action. Do not silently guess.

## 3. Define canonical contracts

Before broad changes, inventory authoritative templates, known-good releases, schemas, and current implementations.

The contract must define:

- semantic roles and legal ordering;
- cardinality;
- TOC inclusion;
- canonical Word style;
- preservation rules;
- release severity;
- deterministic versus LLM ownership;
- source repository and commit provenance for migrated behavior.

## 4. Validate article models

Before normalized DOCX generation, validate at minimum:

- exactly one article title;
- at least one author;
- title is not an abstract heading;
- quoted attribution is not title, author, or affiliation;
- epigraph is not author or affiliation;
- article DOI is found only in the permitted header zone;
- bibliography DOI is not article DOI;
- references heading is not ordinary body text;
- every figure and table has a structural association.

Invalid structure must create `BLOCKED`, `REVIEW`, or an operator action.

## 5. Apply canonical styles

- Import canonical styles from the approved template.
- Do not rely on author-document styles.
- Map every semantic role to one canonical style.
- Remove conflicting direct formatting from structural paragraphs only.
- Preserve meaningful inline formatting, formulas, links, superscript, and subscript.
- Audit unknown style IDs, collisions, and structural direct formatting.

## 6. Merge safely

Preserve and explicitly map:

- styles;
- numbering;
- relationships;
- images and drawings;
- equations;
- hyperlinks;
- bookmarks;
- notes;
- section properties;
- headers and footers;
- tables;
- shapes, SmartArt, textboxes, and OLE objects when present.

Do not assume copied XML references remain valid in the destination package.

## 7. Build TOC from validated data

Do not infer TOC entries by scanning title-like text.

Build from validated article records containing:

- article ID;
- validated title;
- validated authors;
- section;
- stable bookmark;
- actual page number.

Required gates are derived from the manifest:

- expected row count equals actual article rows;
- every title and author matches;
- every page number is numeric and non-empty;
- extras are zero;
- missing rows are zero.

## 8. Repository consolidation

When merging repositories:

1. read `docs/repository-consolidation.json`;
2. identify unique responsibilities, not merely unique filenames;
3. port behavior with provenance and regression tests;
4. keep one deterministic pipeline, one runtime skill bundle, and one CLI entry point;
5. exclude generated journals, private submissions, caches, model weights, virtual environments, and IDE state;
6. mark a source repository `safe_to_retire` only after all retirement gates pass;
7. prefer archiving meaningful history over deletion.

## 9. Run gates

Run, as applicable:

1. unit tests;
2. local-LLM benchmark;
3. structured-article validation;
4. normalized style audit;
5. merge audit;
6. simulation audit;
7. content-integrity audit;
8. style-contract audit;
9. business-rules audit;
10. TOC validation;
11. Word-open/repair check;
12. visual rendering review;
13. repository migration validator;
14. release gate.

Critical failures must not be averaged into a misleading score.

## 10. Create a new run

Never overwrite a baseline run. Use a new timestamped directory and candidate naming until release passes.

## 11. Commit and publish review evidence

Before staging:

- inspect status, branch, remotes, visibility, diff, and file sizes;
- ensure no secrets or prohibited source material are included;
- stage only intended paths;
- never force-push.

Push to a dedicated review branch and create a Draft PR. A blocked candidate may be published for review only when it remains explicitly `BLOCKED` and unresolved gates are visible.
