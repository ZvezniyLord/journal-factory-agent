# Journal Factory repository instructions

## Canonical repository

This repository is the consolidation target for Journal Factory code, Agent Skills, local-LLM orchestration, deterministic QA, and optional developer tooling.

Before changing production behavior, read:

- `docs/REPOSITORY_CONSOLIDATION.md`
- `docs/JOURNAL_FACTORY_FIX_PROTOCOL.md`
- `docs/LLM_FIX_EVAL_PROTOCOL.md`
- the active acceptance criteria under `docs/runs/`, when present

Use the repository skill:

- `$journal-factory-validated-fix`

## Non-negotiable rules

- Author source documents, ETALON files, templates, and prior releases are read-only.
- Never overwrite a previous run. Create a new timestamped workspace.
- Classify each defect as deterministic, LLM-dependent, or operator-only.
- Deterministic code owns DOCX XML, style IDs, numbering, relationships, pagination, TOC rows, bookmarks, integrity audits, and release gates.
- A local LLM may assist only with ambiguous semantic classification and must return schema-valid structured decisions.
- Do not use cloud or production LLM endpoints for private journal material.
- Never invent authors, titles, DOI values, affiliations, dates, references, or scientific content.
- Never weaken a gate merely to obtain `PASS`.
- Do not call an artifact final unless every critical gate passes.
- Do not use broad staging commands when unrelated changes exist.
- Push changes to a review branch and use a Draft PR unless explicitly instructed otherwise.
- Never force-push.

## Consolidation safety

During repository consolidation:

- source repositories are read-only until their unique code, tests, docs, and history are inventoried;
- do not delete or archive a source repository until the migration manifest marks it `safe_to_retire`;
- preserve provenance for imported files in `docs/repository-consolidation.json`;
- do not import generated journals, real submissions, secrets, caches, model weights, virtual environments, or IDE state;
- prefer one implementation per responsibility and delete duplicates only after regression tests prove the canonical implementation.

## Required final report

Report:

- files and repositories inspected;
- root cause and chosen canonical implementation;
- tests and audits run;
- remaining blockers;
- branch, commit, and PR;
- source repositories that are safe to archive or delete;
- source repositories that must remain until migration is complete.
