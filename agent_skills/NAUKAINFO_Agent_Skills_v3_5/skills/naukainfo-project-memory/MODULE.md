---
name: naukainfo-project-memory
description: Updates NAUKAINFO project_memory after a run with verified working solutions, failures, known bugs, visual differences, regression tests, decisions, changelog, and exact artifact paths. Use after every meaningful test, build, repair, or audit.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Procedure

1. Read the memory contract before writing.
2. Record only evidence from completed runs.
3. Update the smallest relevant files:
   - `working_solutions.md` — confirmed working behavior;
   - `failed_attempts.md` — failed approaches and root causes;
   - `known_bugs.md` — reproducible unresolved issues;
   - `regression_tests.md` — tests/fixtures/commands and results;
   - `visual_differences.md` — observed permitted/unintended differences;
   - `decisions.md` — architectural choices and rejected alternatives;
   - `changelog.md` — concise change entry;
   - `todo.md` — next actions.
4. Include run ID, command, input conference, report paths and test results.
5. Do not write unsupported filenames and do not overwrite prior history.

## Quality

Separate fact from inference. Never record “validated” unless a test or audit actually ran.
