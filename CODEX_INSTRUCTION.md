# Codex Operating Instruction — Journal Factory

## Mandatory startup

Before changing anything:

1. Read `AGENTS.md` completely.
2. Read `skills/repository_acceptance/SKILL.md` completely.
3. Read this file completely.
4. Verify repository identity, branch, remote, history, tracked files, untracked files, branches, and tags.
5. Do not trust previous success messages.
6. Do not start implementation while repository acceptance is `BLOCKED`.

## Current repository target

- Repository: `ZvezniyLord/journal-factory-agent`
- Required branch: `main`
- Human entry point in future implementation: root `index.html`
- Architecture: OOP, SOLID, dependency inversion, explicit ports/adapters, no monolithic pipeline.

## Immediate task: verify and finish the clean reset

The repository previously retained legacy Journal Factory MVP files after a claimed reset. Treat the reset as unverified.

### Audit commands

Run and preserve their outputs:

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short
git log --oneline --decorate --graph --all -20
git rev-list --count HEAD
git ls-files
git clean -ndx
git branch -a
git tag --list
git ls-remote --heads origin
git ls-remote --tags origin
```

### Legacy paths that must be removed for the clean bootstrap

Unless the user explicitly approves them later, remove these old tracked or untracked items:

```text
agent_skills/
build/
fixtures/
journal_factory/
schemas/
tests/
Dockerfile
docker-compose.yml
ETALON-JOURNAL.docx
Jurnal.dotx
pytest.ini
requirements.txt
RUN_JOURNAL_FACTORY.cmd
RUN_JOURNAL_FACTORY.ps1
CLEANUP_REPORT.md
```

Also remove any other old MVP source, generated artifact, cache, test fixture, launcher, template, or report not included in the allowlist.

Do not delete `.git`.

Do not delete user data outside the repository root.

Do not run destructive cleanup until `git clean -ndx` has been reviewed.

### Bootstrap allowlist

After cleanup, the only tracked files allowed before Phase 1 implementation are:

```text
.gitignore
AGENTS.md
README.md
CODEX_INSTRUCTION.md
docs/.gitkeep
skills/repository_acceptance/SKILL.md
```

`.idea/` may remain locally for the IDE but must be ignored and untracked.

### Required reset verification

After cleanup run:

```bash
git status --short
git ls-files
git clean -ndx
git log --oneline --decorate --graph --all -20
git branch -a
git tag --list
```

Compare the full result with the bootstrap allowlist. Any unexplained extra path means `BLOCKED`.

Commit cleanup separately with:

```text
chore: complete verified repository reset
```

Push to `main`, then run:

```bash
git fetch origin --prune
git rev-parse HEAD
git rev-parse origin/main
git diff --stat origin/main..HEAD
git ls-tree -r --name-only origin/main
```

Local `HEAD` and `origin/main` must match exactly.

## Cyclic development rule

After the reset passes, work only in short cycles:

`PLAN -> FAILING TEST -> MINIMAL IMPLEMENTATION -> FOCUSED TEST -> FULL TEST -> ARTIFACT INSPECTION -> ARCHITECTURE REVIEW -> FIX -> REPEAT`

After every cycle apply `skills/repository_acceptance/SKILL.md`.

Never proceed to the next cycle with status `BLOCKED`.

## Phase 1 only: Workspace Driver Core and start page

Do not implement Excel, DOCX, article processing, Header Core, marker detection, RAG, LLM calls, journal assembly, rendering, or production formatting yet.

### Cycle 1 — domain configuration

Create tests first for:

- `WorkspaceConfig`;
- journal number validation;
- source directory validation;
- Desktop resolution;
- explicit output-parent override;
- normalized absolute paths.

Implementation must not touch the real Desktop during tests.

### Cycle 2 — workspace layout

Create tests first for immutable `WorkspaceLayout` and these canonical directories:

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

### Cycle 3 — path and report registries

Create tests first for:

- `PathRegistry`;
- `ReportRegistry`;
- absolute normalized paths;
- deterministic UTF-8 JSON;
- no ad-hoc workspace path construction outside the registry.

### Cycle 4 — run and action models

Create tests first for:

- `RunContext`;
- `ActionRecord`;
- `ReportRecord`;
- timestamps and run IDs;
- append-only JSONL action history;
- typed errors.

### Cycle 5 — WorkspaceDriver

Create tests first for:

- directory creation;
- idempotent repeated execution;
- no deletion or overwrite of user files;
- structured return values;
- structured failures without traceback leakage;
- creation of:
  - `reports/run_manifest.json`;
  - `reports/path_registry.json`;
  - `reports/report_registry.json`;
  - `reports/action_log.jsonl`.

`WorkspaceDriver` must not contain HTML, HTTP, Excel, DOCX, LLM, or article logic.

### Cycle 6 — local API

Create and test separately:

- `GET /api/workspace/defaults`;
- `POST /api/workspace/validate`;
- `POST /api/workspace/create`;
- `GET /api/workspace/status`.

Validation must not mutate the filesystem. No Python traceback may be returned to the browser.

### Cycle 7 — root index.html

Create tests first for:

- page loads;
- journal number field;
- source-folder path field and chooser bridge;
- output-parent field and Desktop default;
- computed workspace path;
- disabled create button while invalid;
- validation errors;
- successful workspace result.

HTML contains presentation and interaction only, not domain business logic.

### Cycle 8 — launcher

Create tests first for:

- local bind to `127.0.0.1`;
- automatic browser opening;
- one active server instance;
- occupied-port handling;
- clear shutdown behavior.

### Cycle 9 — integration

Use temporary directories to verify the full flow:

1. request defaults;
2. validate configuration;
3. create workspace;
4. inspect exact folder tree;
5. parse every JSON/JSONL report;
6. repeat create;
7. verify idempotence and user-file safety;
8. request status;
9. verify UI status matches filesystem state.

## Required classes and boundaries

At minimum:

- `WorkspaceConfig`;
- `WorkspaceLayout`;
- `RunContext`;
- `ActionRecord`;
- `ReportRecord`;
- `PathRegistry`;
- `ReportRegistry`;
- `WorkspaceDriverPort`;
- `WorkspaceDriver`;
- `FileSystemAdapter`.

Domain models must not perform filesystem or HTTP work.

HTTP controllers must call application ports and must not create paths themselves.

The browser must not contain filesystem business rules.

## Test rules

- Test-first for every small behavior.
- Use only temporary directories.
- No real Desktop writes.
- No network dependency.
- No Docker dependency.
- No LLM calls.
- No hidden `skip`, `xfail`, disabled tests, or hardcoded success.
- Run focused tests, then the complete suite after every cycle.

## Reporting after every cycle

Print:

- cycle name;
- plan;
- failing test added;
- implementation files changed;
- focused-test command and result;
- full-test command and result;
- artifacts inspected;
- architecture findings;
- repository acceptance findings;
- final cycle status: `CONTINUE` or `BLOCKED`.

## Final Phase 1 gate

Phase 1 is complete only when:

- the repository reset was independently verified;
- the root `index.html` opens through the launcher;
- defaults, validate, create, and status APIs work;
- the exact workspace tree is created;
- all required reports exist and parse;
- repeat execution is safe and idempotent;
- all tests pass with no unexplained skip/xfail;
- no legacy MVP residue remains;
- no future core was implemented;
- architecture review passes;
- `skills/repository_acceptance/SKILL.md` returns `PASS`;
- local `HEAD` equals `origin/main` after push.

Do not claim completion from code generation alone. Show the evidence.
