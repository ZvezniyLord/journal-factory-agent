# HERMES_153_STATELESS_TEST.md

## Goal

Test the new stateless semantic-audit architecture on the existing real conference 153 intake without rebuilding from scratch.

The previous long interactive Hermes sessions are evidence of a controller-context problem. This test must prove that article semantics can be processed in short independent model calls without accumulating 60-100K+ interactive context.

## Workspace

`X:\CODEX_5.5_redactor\Codex_6\056_Asttra`

## Existing run

`runs/153_real_intake/`

Reuse it. Do not delete it.

## Required first step

Sync latest:

- repository: `ZvezniyLord/journal-factory-agent`
- branch: `astra/056-clean-room-skeleton`

Then run:

`.venv\Scripts\python.exe -m pytest -q`

If tests fail, stop and return the failing tests. Do not start semantic inference.

## Why source_index must be regenerated

The new DOCX inspector now emits bounded `semantic_signals` from the full article structure:
- small head window;
- small tail window;
- deterministic role hits across the document;
- role counts.

Therefore regenerate:

`.venv\Scripts\python.exe -m astra_journal.cli source-index runs\153_real_intake\index_root --json runs\153_real_intake\source_index.json`

Then regenerate the manifest using the existing Excel report:

`.venv\Scripts\python.exe -m astra_journal.cli build-manifest runs\153_real_intake\excel.json runs\153_real_intake\source_index.json --json runs\153_real_intake\manifest.json`

## Stateless semantic audit

Do NOT read all articles into the interactive Hermes conversation.

Do NOT manually semantically audit articles in chat.

Instead run Astra's direct stateless semantic-audit command.

Each provider request must contain exactly ONE bounded article packet and no previous article messages.

Run in short resumable steps:

`.venv\Scripts\python.exe -m astra_journal.cli semantic-audit runs\153_real_intake\manifest.json runs\153_real_intake\source_index.json --run-dir runs\153_real_intake --max-new-articles 3`

The command prints only a compact summary.

If status is `INCOMPLETE`, run the same command again.

Repeat until:
- status = `PASS`; or
- status = `BLOCKED`.

Do not send the contents of `semantic_audit.json` back into the interactive conversation.

Do not paste per-article responses into chat.

Astra itself persists each article response under:
`runs/153_real_intake/hermes/responses/`

Successful calls are cached under:
`runs/153_real_intake/hermes/cache/`

If the provider dies between steps, start a fresh controller session later and run the same semantic-audit command. Completed articles must be recovered from cache instead of recomputed.

## Invariants to verify

- architecture = `STATELESS_ONE_ARTICLE_PER_REQUEST`;
- article semantic batch size = 1;
- no semantic packet exceeds configured hard request limits;
- no full journal or full archive is sent to the model;
- no previous article chat history is sent with the next article;
- every response is schema-validated;
- checkpoint occurs after every article;
- cached articles are reused after restart;
- original DOC/DOCX files remain unchanged;
- final journal is NOT created in this test;
- nothing is written to N:;
- persistent Hermes skills are not created or modified.

## Expected semantic fields per matched material

The result on disk should cover:
- author;
- coauthors;
- supervisor;
- affiliation;
- position/degree;
- ORCID;
- title;
- UDC present/missing/review;
- abstract status;
- keywords status;
- table-caption count;
- figure-caption count;
- reference heading;
- references-region status;
- raw section;
- section-mapping status;
- ambiguities.

Deterministic Astra extraction should provide obvious UDC/DOI/ORCID/ABSTRACT/KEYWORDS/TABLE_CAPTION/FIGURE_CAPTION/REF_TITLE evidence before Hermes inference.

## Final controller response

Return only this compact JSON:

{
  "task": "astra_153_stateless_semantic_test",
  "status": "ok|fail|blocked",
  "synced_head": "...",
  "pytest": {
    "passed": 0,
    "failed": 0
  },
  "manifest": {
    "matched": 0,
    "review": 0,
    "coauthors": 0,
    "free_listeners": 0
  },
  "semantic_audit": {
    "architecture": "STATELESS_ONE_ARTICLE_PER_REQUEST",
    "article_count": 0,
    "completed": 0,
    "cached": 0,
    "failed": 0,
    "remaining": 0,
    "controller_steps": 0
  },
  "provider_failures": [],
  "warnings": [],
  "failures": []
}
