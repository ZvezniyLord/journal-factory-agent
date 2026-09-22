# HERMES_NEXT_TASK.md

## Goal

Validate the newest Astra 056 foundation on the operator PC and return deterministic evidence. Do not create a production journal yet.

Local workspace:
`X:\CODEX_5.5_redactor\Codex_6\056_Asttra`

Repository branch:
`astra/056-clean-room-skeleton`

## Important new incident

A real journal exhibited formatting drift after save/close/reopen in Microsoft Word. Root causes included mixed styles, `w:autoRedefine`, theme-font fallback and inherited paragraph settings.

Therefore Word reopen stability is now release-blocking.

Do not repair this by globally changing `Normal`.

## Task

1. Sync the latest branch into the local workspace using the existing sync script.
2. Run `scripts/setup_local_env.ps1`.
3. Verify Python is:
   `X:\CODEX_5.5_redactor\Codex_6\056_Asttra\.venv\Scripts\python.exe`
4. Run all tests:
   `.venv\Scripts\python.exe -m pytest -q`
5. Generate the synthetic golden fixture:
   `.venv\Scripts\python.exe -m astra_journal.cli make-golden-fixture runs\validation\golden.docx`
6. Audit it:
   `.venv\Scripts\python.exe -m astra_journal.cli audit-docx runs\validation\golden.docx --json runs\validation\golden_audit.json`
7. Run Microsoft Word COM save-close-reopen:
   `.venv\Scripts\python.exe -m astra_journal.cli word-roundtrip runs\validation\golden.docx runs\validation\golden_word_roundtrip.docx --json runs\validation\word_roundtrip.json`
8. Re-audit the Word-produced file.
9. Verify both reference-list instances remain structurally independent and start at 1.
10. Verify bold, italic, underline, subscript, superscript, table, image and hyperlink survived.
11. Verify no canonical Astra body style uses `autoRedefine` or theme-font fallback.
12. If Word COM is unavailable, return BLOCKED and exact diagnostics; do not fake PASS.

## Intake smoke tests

If the operator provides sample paths, run:

`astra-journal inspect-excel <xlsx> --json runs\validation\excel.json`

`astra-journal inspect-source <docx> --json runs\validation\source.json`

Do not read or summarize full archives into chat context. Use compact JSON only.

## Forbidden

- do not inspect parent/sibling legacy project code;
- do not create persistent self-improvement skills;
- do not mutate source DOCX files;
- do not make a production journal yet;
- do not claim release readiness from unit tests alone.

## Return JSON only

{
  "task": "astra_056_local_validation",
  "status": "ok|fail|blocked",
  "branch_head": "...",
  "python_path": "...",
  "pytest": {
    "passed": 0,
    "failed": 0
  },
  "golden_fixture": "PASS|FAIL",
  "word_com_roundtrip": "PASS|FAIL|BLOCKED",
  "reference_restart": "PASS|FAIL",
  "formatting_survival": "PASS|FAIL",
  "style_stability": "PASS|FAIL",
  "warnings": [],
  "failures": []
}
