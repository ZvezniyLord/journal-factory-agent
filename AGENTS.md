# AGENTS.md — Journal Factory

## Mandatory navigation for every new agent chat

This file is the starting point and reading router for the repository.

Do not rely on chat memory, a copied prompt, prior success messages, or commit titles. Repository documents are the persistent source of truth.

Follow this sequence exactly:

1. Read this `AGENTS.md` completely.
2. Open and read `docs/NEW_CHAT_START.md` completely.
3. Return to this file.
4. Open and read `docs/BUSINESS_LOGIC_AND_ROADMAP.md` completely.
5. Return to this file.
6. Open and read `CODEX_INSTRUCTION.md` completely.
7. Return to this file.
8. Open and read `skills/repository_acceptance/SKILL.md` completely.
9. Return to this file.
10. Perform the repository acceptance audit before modifying code.
11. Begin only the currently approved development cycle.

No referenced document may be replaced by a summary. Do not skip ahead.

## Document responsibilities

- `docs/NEW_CHAT_START.md` — canonical startup protocol for a fresh Codex/Sol chat, current Phase 1 cycle order, testing, real-run, user-testing, and reporting rules.
- `docs/BUSINESS_LOGIC_AND_ROADMAP.md` — complete product business logic, all cores, system workflow, quality rules, and long-term roadmap.
- `CODEX_INSTRUCTION.md` — technical implementation contract, cleanup rules, current classes, APIs, tests, and phase gates.
- `skills/repository_acceptance/SKILL.md` — mandatory independent verification after every cleanup, cycle, migration, or implementation stage.

When documents appear to conflict, stop with `BLOCKED`, quote the conflicting requirements, and request resolution. Do not silently choose one.

## Product purpose

Journal Factory is a local, browser-driven system for discovering conference source files, matching Excel registry records to article documents, transforming each article independently, assembling the final journal, rendering it, and validating the result.

The architecture must follow OOP, SOLID, dependency inversion, explicit ports and adapters, typed errors, deterministic core logic, and test-first development. A monolithic linear script is forbidden.

## Non-negotiable universal document invariant

After the dashboard and workspace are created, the first document-editing operation is universal normalization.

Every editable text element in every transformed article and assembled journal must use:

- font size: **11 pt**;
- line spacing: **1.0 / single**.

This applies without exception to body text, article headers, authors, affiliations, UDC, titles, annotations, keywords, headings, table cells, captions, figure labels stored as editable text, references, bibliography entries, headers, footers, notes, and service text.

Rasterized text inside an image cannot be reformatted, but its caption and every editable surrounding object must follow the rule. Any editable production text violating 11 pt or 1.0 is a hard `FAIL`.

## Single human entry point

The root `index.html`, served by a local backend on `127.0.0.1`, is the only normal human-facing entry point.

The browser interface must eventually allow the operator to:

- select the source folder;
- select the output parent;
- use a Desktop default named by journal/conference number;
- review the journal number;
- start, inspect, pause where supported, and resume the pipeline;
- inspect every core, article, warning, LLM call, match score, report, and final quality gate.

Business logic must not live in HTML.

## Core architecture summary

The detailed contracts live in `docs/BUSINESS_LOGIC_AND_ROADMAP.md`.

Approved cores include:

1. Workspace Driver Core
2. Browser UI Core
3. Source Discovery Core
4. Source Snapshot Core
5. Excel Registry Core
6. Retrieval and Matching Core
7. Article Processing Coordinator
8. Marker Knowledge Core
9. Article Segmentation Core
10. Header Core
11. Document Normalization Core
12. Table Core
13. Figure Core
14. Reference Core
15. Assembly Core
16. Rendering Core
17. QA Core
18. Reporting and Dashboard Core

Each core must expose an explicit interface and machine-readable reports. Deterministic Python logic is primary. A local LLM is allowed only for unresolved ambiguity through a logged decision contract.

## Workspace authority

`WorkspaceDriver` and its class family own only:

- source and output paths;
- run identity;
- journal number;
- canonical directory creation;
- path registry;
- run context;
- action history;
- report registry;
- persisted run state.

Required abstractions:

- `WorkspaceConfig`
- `WorkspaceLayout`
- `RunContext`
- `ActionRecord`
- `ReportRecord`
- `PathRegistry`
- `ReportRegistry`
- `WorkspaceDriverPort`
- `WorkspaceDriver`
- `FileSystemAdapter`

All other cores receive paths through `WorkspaceDriverPort`. They must not construct ad-hoc absolute workspace paths.

Canonical workspace directories:

```text
source_snapshot/
articles_raw/
articles_transformed/
reports/
logs/
database/
rendered/pdf/
rendered/png/
final/
temp/
```

Required persisted reports:

- `reports/run_manifest.json`
- `reports/action_log.jsonl`
- `reports/path_registry.json`
- `reports/report_registry.json`
- `reports/run_summary.html`

## Current approved scope

The current approved scope is **Phase 1 only**.

Phase 1 includes:

- root `index.html`;
- local backend and launcher;
- source-folder selection or bridge;
- output-parent selection or bridge;
- journal number;
- Desktop default;
- computed workspace path;
- Workspace Driver class family;
- defaults, validate, create, and status APIs;
- canonical workspace creation;
- deterministic JSON/JSONL reports;
- automated tests;
- real launch and user manual testing.

Do not implement before Phase 1 is accepted:

- Excel parsing;
- DOC/DOCX parsing or editing;
- Header Core;
- marker detection;
- article transformation;
- retrieval/RAG;
- embeddings;
- local LLM integration;
- journal assembly;
- document formatting implementation;
- PDF/PNG rendering;
- production document QA.

The detailed Phase 1 cycles and fresh-chat first action are defined in `docs/NEW_CHAT_START.md` and `CODEX_INSTRUCTION.md`.

## Mandatory development loop

Every cycle uses:

`PLAN -> FAILING TEST -> MINIMAL IMPLEMENTATION -> FOCUSED TEST -> FULL TEST SUITE -> REAL RUN -> ARTIFACT INSPECTION -> ARCHITECTURE REVIEW -> REPOSITORY ACCEPTANCE -> FIX -> REPEAT`

After every cycle apply `skills/repository_acceptance/SKILL.md`.

Never proceed while status is `BLOCKED`.

After every externally visible cycle, provide exact manual-test instructions and stop with `STATUS: WAITING FOR USER` until the user reports the result.

## Output quality gate

Production output is not ready unless the final quality report explicitly marks it ready.

Allowed final states:

- `PASS`
- `PASS WITH WARNINGS`
- `FAIL`

A draft DOCX must never be presented as final without the quality gate.

## First instruction to a fresh Codex/Sol chat

The only message needed from the user is:

```text
Open AGENTS.md in the repository and follow its mandatory navigation exactly. Start only the currently approved cycle, perform all tests and real-run checks, give me the manual test, then stop and wait for my result.
```

Everything else must be loaded from the repository documents.