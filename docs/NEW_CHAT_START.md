# New Chat Startup Protocol — Journal Factory

This document is the canonical startup instruction for every new Codex/Sol development chat.

## Operating rule

Do not rely on chat memory or a copied prompt. Treat the repository documents as the only persistent source of truth.

At the beginning of every new chat:

1. Open and read `AGENTS.md` completely.
2. Follow its reading order exactly.
3. Read every referenced document completely before editing code.
4. Return to `AGENTS.md` after each referenced document and continue with the next item.
5. Do not infer completion from prior messages, commit titles, or the existence of one expected file.
6. Verify the actual local and remote repository state before development.

## Mandatory reading chain

Read in this order:

1. `AGENTS.md` — navigation, global laws, current phase.
2. `docs/NEW_CHAT_START.md` — this startup protocol.
3. `docs/BUSINESS_LOGIC_AND_ROADMAP.md` — complete product business logic and development roadmap.
4. `CODEX_INSTRUCTION.md` — current implementation cycles and technical acceptance requirements.
5. `skills/repository_acceptance/SKILL.md` — independent verification after every cycle.

No document may be replaced by a summary.

## Repository acceptance before work

Run and preserve the output of:

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short
git log --oneline --decorate --graph --all -20
git ls-files
git clean -ndx
git branch -a
git tag --list
git ls-remote --heads origin
git ls-remote --tags origin
git rev-parse HEAD
git rev-parse origin/main
```

Acceptance requires:

- repository root is the intended project;
- `origin` is `ZvezniyLord/journal-factory-agent`;
- active branch is `main`, unless the task explicitly says otherwise;
- local `HEAD` equals `origin/main` before a new development cycle;
- no unexplained tracked, untracked, ignored, branch, or tag residue exists;
- no legacy Journal Factory MVP files remain;
- repository state matches the allowlist for the current phase.

Any discrepancy means `BLOCKED`. Do not begin implementation.

## Development loop

Every development cycle must use:

`PLAN -> FAILING TEST -> MINIMAL IMPLEMENTATION -> FOCUSED TEST -> FULL TEST SUITE -> REAL RUN -> ARTIFACT INSPECTION -> ARCHITECTURE REVIEW -> REPOSITORY ACCEPTANCE -> FIX -> REPEAT`

Rules:

- keep each cycle small and atomic;
- do not implement several cores at once;
- write a failing test before the behavior;
- run focused tests and then the complete suite;
- run the component or application for real;
- inspect actual generated files and responses;
- apply `skills/repository_acceptance/SKILL.md` after every cycle;
- stop on `BLOCKED`;
- make one atomic commit only after all gates pass;
- do not push automatically without explicit permission;
- never report completion from code generation alone.

## User testing gate

After every externally visible cycle:

1. start the relevant component;
2. provide the exact launch command;
3. provide exact manual-test steps;
4. state the expected result;
5. stop with `STATUS: WAITING FOR USER`;
6. do not begin the next externally visible cycle until the user reports the result.

## Current development scope

The current approved scope is Phase 1 only:

- root `index.html` as the only human-facing entry point;
- local backend on `127.0.0.1`;
- launcher;
- source-folder selection or bridge;
- output-parent selection or bridge;
- journal number;
- Desktop default output parent;
- computed workspace path;
- `WorkspaceConfig`;
- `WorkspaceLayout`;
- `RunContext`;
- `ActionRecord`;
- `ReportRecord`;
- `PathRegistry`;
- `ReportRegistry`;
- `WorkspaceDriverPort`;
- `WorkspaceDriver`;
- `FileSystemAdapter`;
- workspace defaults, validate, create, and status APIs;
- canonical workspace directory creation;
- deterministic JSON/JSONL reports;
- automated tests and real manual launch.

Do not implement yet:

- Excel parsing;
- DOC/DOCX parsing or editing;
- Header Core;
- marker detection;
- article processing;
- retrieval/RAG;
- embeddings;
- local LLM integration;
- journal assembly;
- universal document formatting implementation;
- rendering to PDF/PNG;
- production document QA.

## Phase 1 cycle order

### Cycle 1 — bootstrap and skeleton

- verify repository acceptance;
- choose the minimal Python stack;
- create the project structure;
- configure the test runner;
- add a smoke test;
- add a launcher/backend smoke test;
- document installation, test, and run commands;
- perform a real launch;
- provide `MANUAL TEST 1`;
- stop and wait for the user.

### Cycle 2 — WorkspaceConfig

Implement only after Cycle 1 manual approval:

- journal-number validation;
- source-directory validation;
- explicit output-parent handling;
- Desktop default resolution;
- normalized absolute paths;
- tests using temporary directories only.

### Cycle 3 — WorkspaceLayout and PathRegistry

- immutable canonical layout;
- all required workspace paths;
- deterministic path registry;
- no ad-hoc absolute path construction elsewhere.

### Cycle 4 — run and report models

- `RunContext`;
- `ActionRecord`;
- `ReportRecord`;
- `ReportRegistry`;
- append-only action log;
- deterministic JSON and JSONL.

### Cycle 5 — WorkspaceDriver

- safe workspace creation;
- exact canonical tree;
- idempotent or collision-safe repeat behavior;
- typed failures;
- no deletion or silent overwrite of user files;
- required reports.

### Cycle 6 — local API

Implement and test:

- `GET /api/workspace/defaults`;
- `POST /api/workspace/validate`;
- `POST /api/workspace/create`;
- `GET /api/workspace/status`.

Validation must not mutate the filesystem. Tracebacks must not reach the browser.

### Cycle 7 — root index.html

- journal number;
- source folder;
- output parent;
- Desktop default;
- calculated workspace path;
- validation state;
- create button;
- clear structured errors and result status;
- presentation only, no domain business logic.

### Cycle 8 — launcher

- bind to `127.0.0.1`;
- open the browser automatically;
- handle occupied ports;
- prevent accidental duplicate instances;
- provide clear shutdown behavior.

### Cycle 9 — Phase 1 integration

Verify the complete flow:

`defaults -> validate -> create -> filesystem tree -> reports -> repeat create -> status -> UI reconstruction`

## Canonical workspace tree

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

Required reports:

- `reports/run_manifest.json`;
- `reports/path_registry.json`;
- `reports/report_registry.json`;
- `reports/action_log.jsonl`;
- `reports/run_summary.html`.

## Architecture boundaries

- OOP, SOLID, dependency inversion, ports and adapters;
- typed models and typed errors;
- domain models perform no filesystem or HTTP I/O;
- filesystem access goes through an adapter;
- HTTP controllers call application ports;
- HTML contains no filesystem or document business logic;
- `WorkspaceDriver` contains no HTML, HTTP, Excel, DOCX, article, or LLM logic;
- all workspace paths come through `PathRegistry` and `WorkspaceDriverPort`;
- source files are never modified in place;
- no monolithic pipeline script.

## Test rules

- test first for each behavior;
- use temporary directories;
- no real Desktop writes in automated tests;
- no network dependency;
- no Docker dependency;
- no LLM calls;
- no hidden `skip`, `xfail`, disabled tests, or hardcoded success;
- run focused and full tests after each change;
- report exact command, passed, failed, skipped, and duration.

## Required cycle report format

Every cycle report must contain exactly these sections:

- `CYCLE`
- `PLAN`
- `FAILING TEST ADDED`
- `IMPLEMENTATION`
- `FILES CHANGED`
- `COMMANDS RUN`
- `TEST RESULTS`
- `REAL RUN RESULTS`
- `ARTIFACTS INSPECTED`
- `ARCHITECTURE REVIEW`
- `REPOSITORY ACCEPTANCE`
- `MANUAL TEST FOR USER`
- `KNOWN LIMITATIONS`
- `STATUS: WAITING FOR USER` or `STATUS: BLOCKED`

## First action in a fresh chat

Perform only:

1. complete mandatory reading;
2. repository acceptance audit;
3. Cycle 1 bootstrap and project skeleton;
4. automated tests;
5. real launch;
6. `MANUAL TEST 1`;
7. stop with `STATUS: WAITING FOR USER`.

Do not begin Cycle 2 until the user confirms the manual test result.