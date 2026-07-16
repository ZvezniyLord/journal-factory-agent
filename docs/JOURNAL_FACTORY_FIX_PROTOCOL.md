# Journal Factory fix and release protocol

## Purpose

This document defines the permanent engineering workflow for correcting Journal Factory defects and proving journal readiness. It applies to DOCX structure, style systems, article classification, content preservation, TOC generation, audits, local LLM use, and review publishing.

## Core principle

Use:

`reproduce → measure → prove a candidate → change code → regression test → new run → independent audits → visual validation → release gate`

Never use:

`change code → run once → assume success`

## Separation of responsibilities

### Local Gemma

A configured local Gemma model may assist with ambiguous semantic classification. It is not authoritative for deterministic document mechanics.

Use it for:

- ambiguous title or header classification;
- epigraph versus affiliation;
- translated-title semantic matching;
- ambiguous semantic role proposals.

Do not use it for:

- style IDs;
- DOCX XML mappings;
- numbering IDs;
- page numbers;
- table counts;
- bookmark targets;
- repair warnings;
- release decisions.

### Deterministic code

Deterministic code must own:

- structured article schemas;
- canonical role-to-style mapping;
- merge mappings;
- content/object integrity;
- TOC rows and bookmarks;
- pagination and field updates;
- Word repair validation;
- release gates.

## Phase A — inventory and contracts

1. Inventory reference templates and known-good journals.
2. Select and justify the canonical style source.
3. Extract style, numbering, section, and table contracts.
4. Document semantic roles and legal article structure.
5. Identify operator-only decisions.

No production code changes before the contract exists.

## Phase B — defect reproduction

For each defect:

1. preserve the original failing artifact;
2. create a minimal fixture;
3. identify the exact module and rule;
4. create a failing test;
5. classify the defect as LLM-dependent or deterministic;
6. capture baseline output.

## Phase C — candidate proof

### LLM-dependent proof

Follow `docs/LLM_FIX_EVAL_PROTOCOL.md`.

### Deterministic proof

1. create a test against the contract;
2. implement the minimal candidate in an isolated branch or controlled patch;
3. run focused tests;
4. inspect DOCX package XML where relevant;
5. verify no regression in other fixtures.

## Phase D — production change

Only after candidate proof:

1. update production code;
2. add permanent regression tests;
3. run the complete suite;
4. document root cause and behavior change.

## Phase E — new build

Create a new timestamped run.

Required sequence:

1. inventory;
2. manifest;
3. matching;
4. structured classification;
5. schema validation;
6. normalization;
7. normalized style audit;
8. assembly;
9. merge audit;
10. TOC generation;
11. repagination and field update;
12. verification;
13. simulation audit;
14. content integrity;
15. style-contract audit;
16. business-rules audit;
17. TOC validation;
18. visual render;
19. release gate.

## Phase F — release gates

A release must fail or block if any critical gate fails.

Required PASS conditions:

- expected article count from the validated manifest;
- one validated title per article;
- title and author match for every TOC row;
- numeric page number for every TOC row;
- TOC extras and missing both zero;
- text, image, table, object, and formula loss zero;
- article table count excludes TOC;
- style contract PASS;
- business rules PASS;
- simulation audit has no failed or critical findings;
- Word opens without repair;
- operator blockers zero;
- visual validation PASS.

## Phase G — review publishing

A candidate may be pushed for external review while operator blockers remain, provided it is clearly marked `BLOCKED`.

Publish only curated review artifacts, evidence, code, and tests. Do not publish raw sensitive source material merely because it exists in a run directory.

Use a dedicated review branch and Draft PR. Never force push.
