# AGENTS.md — Journal Factory

## Purpose

Journal Factory is a local, browser-driven system for discovering conference source files, matching Excel registry records to article documents, transforming each article independently, assembling the final journal, rendering it, and validating the result.

The architecture must follow OOP, SOLID, dependency inversion, explicit interfaces, and test-first development. A monolithic linear script is forbidden.

## Universal formatting invariant

The first document-editing operation after the dashboard and workspace are created is universal normalization.

Every editable text element in every transformed article and in the assembled journal must use:

- font size: **11 pt**;
- line spacing: **1.0 (single)**.

This applies without exception to body text, author blocks, affiliations, UDC, annotations, keywords, headings, table text, captions, figure labels stored as editable text, references, bibliography entries, headers, footers, notes, and service text.

Rasterized text inside an image cannot be reformatted, but its caption and all editable surrounding text must follow the rule. Any editable 14 pt text in production output is a hard failure.

## Single human entry point

The single human entry point is the root `index.html` opened in a supported browser.

The interface must let the operator:

1. choose the source folder containing raw conference files;
2. choose the output parent folder;
3. see a default output proposal on the Desktop named by journal/conference number;
4. review the detected journal number before start;
5. start, pause where supported, inspect, and resume the pipeline;
6. inspect every core, article, warning, LLM call, match score, report, and final quality gate.

A plain browser page cannot safely read arbitrary local paths by text input alone. The implementation must use a local backend/desktop bridge while preserving `index.html` as the only human-facing entry point.

## Core architecture

### 1. Workspace Driver Core

This is a dedicated kernel and class family responsible only for paths, run identity, workspace creation, action history, and report locations.

Recommended primary class name:

`WorkspaceDriver`

Responsibilities:

- accept the source path selected by the operator;
- accept or derive the output parent path;
- detect or receive the journal number;
- default the output path to `<Desktop>/<journal_number>`;
- create a collision-safe run directory when needed;
- create and expose canonical subdirectories;
- remember every resolved path used during the run;
- record every material action in chronological order;
- generate machine-readable and human-readable run reports;
- never parse DOCX, Excel, or article semantics itself.

Required canonical directories inside a run:

- `source_snapshot/` — immutable copied source files;
- `articles_raw/` — discovered article files copied as separate originals;
- `articles_transformed/` — one independently transformed article per file;
- `reports/` — JSON, JSONL, CSV, and HTML reports;
- `logs/` — operational logs;
- `database/` — local retrieval/index data;
- `rendered/pdf/` — PDFs;
- `rendered/png/` — page images;
- `final/` — final DOCX and approved outputs;
- `temp/` — disposable working files.

Required abstractions:

- `WorkspaceConfig` — immutable input configuration;
- `WorkspaceLayout` — immutable resolved paths;
- `RunContext` — run id, timestamps, journal number, mode, and current state;
- `ActionRecord` — timestamped event with core, action, status, inputs, outputs, and error data;
- `PathRegistry` — canonical path keys mapped to absolute normalized paths;
- `ReportRegistry` — report names, formats, producers, and paths;
- `WorkspaceDriver` — orchestrates only workspace/path lifecycle;
- `WorkspaceDriverPort` — interface consumed by other cores;
- `FileSystemAdapter` — platform-specific filesystem implementation.

The driver must persist at minimum:

- `reports/run_manifest.json`;
- `reports/action_log.jsonl`;
- `reports/path_registry.json`;
- `reports/report_registry.json`;
- `reports/run_summary.html`.

All cores receive paths through `WorkspaceDriverPort`; they must not construct ad-hoc absolute paths.

### 2. Browser UI Core

Owns `index.html`, UI state, visual pipeline map, progress, warnings, article cards, and operator decisions. It does not contain business logic.

### 3. Source Discovery Core

Recursively discovers Excel files, DOC/DOCX articles, templates, archives, and supporting assets. It reports candidates and never guesses silently.

### 4. Excel Registry Core

Reads and normalizes conference metadata, journal number, sections, authors, titles, ordering, and identifiers.

### 5. Retrieval and Matching Core

Uses deterministic normalization first, then a local retrieval database/RAG-equivalent layer for multilingual author matching, transliteration, aliases, weighted comparison, and confidence scores.

A small local LLM may be called only for ambiguous cases through an explicit decision contract. Every call must be logged with inputs, output, confidence, and reason.

### 6. Article Segmentation Core

Processes each article independently so that its content fits local LLM context limits. It detects recurring structural markers such as:

- UDC / УДК;
- annotation / abstract / анотація;
- keywords / key words / ключові слова;
- table / таблиця;
- figure / рисунок / рис.;
- references / bibliography / список використаних джерел / література;
- other repeated multilingual heading-like markers found in the journal corpus.

### 7. Header Core

A separate dedicated kernel responsible only for the article header (“шапка”): UDC, authors, degrees, positions, affiliations, city/country, title, ordering, language variants, and boundaries between header and article body.

It must combine deterministic rules, marker evidence, visual/style evidence, Excel evidence, retrieval matches, and LLM arbitration only when ambiguity remains.

### 8. Document Normalization Core

Applies the universal 11 pt / 1.0 invariant to every editable text element before further style routing. It must verify the result after writing.

### 9. Assembly Core

Combines transformed articles in Excel order and builds front matter, sections, TOC, pagination, and final DOCX.

### 10. Rendering and QA Core

Renders DOCX to PDF and PNG, performs structural and visual checks, and emits `PASS`, `PASS WITH WARNINGS`, or `FAIL`.

A violation of 11 pt or 1.0 in any editable production text is always `FAIL`.

## Dashboard timing

The dashboard/workspace is created before document normalization and remains available through the entire run. It must show live state from the action log and report registry.

## Development order

Development proceeds in small test-driven stages.

Phase 1 is only:

1. `index.html` as the visible entry point;
2. source-folder selection;
3. output-parent selection;
4. default output proposal `<Desktop>/<journal_number>`;
5. `WorkspaceDriver` creation;
6. canonical directory creation;
7. path/action/report persistence;
8. tests for all of the above.

Do not implement article parsing, DOCX editing, matching, RAG, LLM calls, or assembly before Phase 1 tests pass.

## Phase 1 acceptance tests

At minimum, tests must prove:

- an explicit source path is normalized and stored;
- an explicit output path overrides the default;
- with no explicit output path, Desktop plus journal number is used;
- missing journal number blocks creation or requests operator confirmation;
- unsafe journal numbers are sanitized deterministically;
- repeated runs never overwrite an existing run silently;
- every canonical directory is created;
- all paths are absolute and represented in `path_registry.json`;
- every creation step produces an `ActionRecord` in `action_log.jsonl`;
- report paths are registered in `report_registry.json`;
- filesystem failures return a typed failure and are visible in the UI;
- UI state can be reconstructed from persisted run reports;
- no other core constructs its own absolute workspace paths.

## Output quality gate

Production output is not ready unless the final quality report explicitly marks it ready. Draft DOCX files must never be presented as final without the quality gate.