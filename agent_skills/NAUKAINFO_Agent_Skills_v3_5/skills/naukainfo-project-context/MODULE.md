---
name: naukainfo-project-context
description: Reads NAUKAINFO architecture, project_memory, conventions, known bugs, prior decisions, tests, and existing modules before any code or journal operation. Use at the start of every Journal Builder task, code change, audit, or production run.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

Load only the project-specific facts needed for the current task and prevent repeated mistakes.

## Procedure

1. Call `read_project_context` with the project root.
2. Read, when present: architecture, LLM policy, project conventions, decisions, known bugs, failed attempts, working solutions, regression tests and TODO.
3. Search the repository for an existing implementation before proposing new code.
4. Produce a compact context packet:
   - immutable inputs;
   - allowed changes;
   - relevant existing modules;
   - known regressions;
   - tests that protect this area.
5. Do not begin write operations until contradictions are resolved.

## Gotchas

- The new minimal-authenticity concept differs from old aggressive style normalization.
- `ETALON-JOURNAL.docx` is a master shell, never an output target.
- Some legacy code may exist after an early `return`; do not assume search results are active execution paths.
- Project memory is a contract: only supported files should be updated.

## Done when

The agent can state which existing code it will reuse and which files are protected.
