# Repository Acceptance Verification Skill

## Purpose

This skill is mandatory after every Codex cycle, cleanup, reset, migration, or implementation stage. No stage is accepted from a success message alone. Acceptance is based only on independently verified repository evidence.

## Core rule

Never infer completion from a commit title, a green message, or the existence of one expected file. Verify the complete repository state.

Required loop:

`INSPECT -> COMPARE -> TEST -> VERIFY ARTIFACTS -> REVIEW -> FIX -> REPEAT`

If any check fails, status is `BLOCKED`; do not start the next stage.

## 1. Repository identity

Verify and record:

```bash
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short
```

Acceptance requires:

- the local root is the intended project directory;
- `origin` points to `ZvezniyLord/journal-factory-agent`;
- the active branch is `main` unless a task explicitly requires another branch;
- no unexplained local changes exist.

## 2. Tracked and untracked inventory

Run:

```bash
git ls-files
git status --short
git clean -ndx
```

Compare every tracked and untracked path with the stage allowlist.

Do not use a visual IDE tree as the only source of truth. IDE trees may show ignored, stale, generated, or external files.

Never run `git clean -fdx` before reviewing the dry-run output and protecting user data.

## 3. History verification

Run:

```bash
git log --oneline --decorate --graph --all -20
git rev-list --count HEAD
git show --stat --oneline HEAD
```

For a claimed reset, verify that the history itself matches the reset contract. Deleting files in a new commit is not equivalent to replacing old history.

For an intentionally clean bootstrap, compare the commit count, parent chain, and expected initial commit.

## 4. Branch and tag verification

Run:

```bash
git branch -a
git tag --list
git ls-remote --heads origin
git ls-remote --tags origin
```

Confirm that obsolete local branches, remote branches, and tags are absent when the task required their removal.

## 5. Tree and allowlist verification

Produce a deterministic tree excluding `.git` and approved IDE metadata.

PowerShell example:

```powershell
Get-ChildItem -Force -Recurse |
  Where-Object { $_.FullName -notmatch '\\.git(\\|$)' } |
  ForEach-Object { $_.FullName }
```

Compare the result with the exact allowlist for the current stage.

For the clean bootstrap stage, the expected tracked files are:

```text
.gitignore
AGENTS.md
README.md
docs/.gitkeep
skills/repository_acceptance/SKILL.md
CODEX_INSTRUCTION.md
```

Any additional tracked old launcher, Docker file, Python package, fixture, template, build output, or old report is a failure unless explicitly approved by the current stage.

## 6. Forbidden legacy residue check

For a clean Journal Factory reset, explicitly check that these paths do not remain unless reintroduced by an approved later phase:

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

Check both Git and the local filesystem.

## 7. Test verification

For implementation stages:

1. Run focused tests for the changed unit.
2. Run the complete test suite.
3. Confirm no unexpected `skip`, `xfail`, disabled test, hidden failure, or hardcoded success.
4. Record exact command, pass count, failure count, skipped count, and duration.

A stage is not accepted when tests were not run in the current repository state.

## 8. Artifact verification

Inspect generated artifacts, not only logs.

For workspace stages verify:

- exact directory tree;
- JSON and JSONL files parse successfully;
- required keys and absolute paths exist;
- repeated execution is idempotent;
- user files are not deleted or overwritten;
- UI status corresponds to actual filesystem state.

For document stages verify DOCX internals, rendered PDF/PNG, and final quality reports independently.

## 9. Architecture verification

Check that the implementation follows `AGENTS.md`:

- OOP and SOLID boundaries;
- dependency inversion;
- no monolithic script;
- no business logic in HTML;
- no HTTP responsibilities in domain drivers;
- no ad-hoc absolute path construction outside `PathRegistry`;
- no unapproved implementation of future cores.

## 10. Remote verification after push

After committing and pushing, fetch and compare remote state:

```bash
git fetch origin --prune
git status
git rev-parse HEAD
git rev-parse origin/main
git diff --stat origin/main..HEAD
git ls-tree -r --name-only origin/main
```

Acceptance requires local `HEAD` and `origin/main` to match, unless the task explicitly says not to push.

## 11. Required acceptance report

After every cycle produce a report containing:

- repository root;
- remote URL;
- active branch;
- current commit SHA;
- local/remote equality;
- tracked-file inventory;
- untracked/ignored dry-run inventory;
- branch and tag inventory;
- test commands and results;
- generated artifacts inspected;
- architecture review;
- discrepancies found;
- changes made to fix them;
- final status: `PASS`, `PASS WITH WARNINGS`, or `BLOCKED`.

## 12. No false completion

Never report completion when:

- only a commit message was checked;
- only GitHub history was checked without file inventory;
- only the IDE tree was checked;
- local and remote repositories were not compared;
- old files remain outside Git tracking;
- tests were skipped;
- generated outputs were not inspected;
- a required cleanup lacks an exact allowlist comparison;
- any uncertainty remains about repository identity.

When evidence is incomplete, report exactly what is unknown and return `BLOCKED`.
