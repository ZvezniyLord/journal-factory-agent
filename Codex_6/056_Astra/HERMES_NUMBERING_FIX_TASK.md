# HERMES_NUMBERING_FIX_TASK.md

## Current blocker

The first Word COM golden validation found a release-blocking defect:

Before Microsoft Word save:
- article 1 bibliography used its own numbering instance;
- article 2 bibliography used another numbering instance;
- both visibly started at 1.

After Word SaveAs2 -> Close -> Reopen:
- Word deduplicated/canonicalized the numbering definitions;
- all reference paragraphs were rebound to one logical list;
- article 2 continued as 3, 4 instead of restarting at 1.

This is documented in `NUMBERING_INCIDENT_001.md`.

## Goal

Find and validate a Microsoft-Word-stable bibliography restart strategy, then update only the Astra numbering/golden-fixture code needed to use it.

Do not build a production journal yet.

## Local workspace

`X:\CODEX_5.5_redactor\Codex_6\056_Asttra`

## Required first step

Sync the latest branch:

`astra/056-clean-room-skeleton`

Expected current branch head at task creation:

`3516611eba69c57e43a915f8e3b0aa93f015cad3`

After sync read only:
- `NUMBERING_INCIDENT_001.md`
- `HERMES_NUMBERING_FIX_TASK.md`
- `EDITORIAL_RULES.md`
- `naukainfo.yaml`
- `config/role_rules.yaml`
- `config/sections.yaml`
- the numbering-related code/tests.

Do not summarize the whole folder.

## Experiment matrix

Create experiments under:

`runs/validation/numbering_matrix/`

Do not touch source conference documents.

Generate a synthetic document with at least 3 articles and 2 references per article.

Each article must have:
- a `REFERENCES` heading;
- two true Word numbered reference paragraphs;
- an unnumbered DOI/URL continuation paragraph after the numbered references.

Test these strategies:

A. Current control:
- separate structurally identical abstractNum;
- separate num;
- startOverride=1.

B. Shared abstractNum:
- one abstractNum;
- separate num instances;
- first list uses abstract start=1;
- subsequent num instances use explicit startOverride=1.

C. Per-article abstractNum with unique Word list identity:
- unique abstractNum per article;
- unique `w:nsid`;
- unique `w:tmpl`;
- separate num per article;
- start=1.

D. C plus explicit lvlOverride/startOverride=1 on each article num.

You may add one additional candidate only if A-D all fail and you can justify it from actual Word behavior.

## Word validation

For every candidate:

1. Save initial DOCX.
2. Probe Word-visible list values before roundtrip.
3. Microsoft Word COM SaveAs2 -> Close -> Reopen.
4. Probe Word-visible list values after roundtrip.
5. Perform a SECOND Word SaveAs2 -> Close -> Reopen on the already Word-produced file.
6. Probe again.
7. Inspect numbering.xml after both rounds.

Use the repository CLI:

`astra-journal word-list-probe <docx> --json <output.json>`

and:

`astra-journal word-roundtrip <source> <destination> --json <output.json>`

A strategy passes only if BOTH Word roundtrips show this visible sequence:

Article 1: 1, 2
Article 2: 1, 2
Article 3: 1, 2

The DOI/URL continuation paragraphs must remain unnumbered.

No manual right-click "Start at 1" is allowed.

## Acceptance

The winning strategy must:
- survive two consecutive Microsoft Word save-close-reopen cycles;
- preserve true automatic Word numbering;
- preserve REFER style;
- not type visible numbers into reference text;
- keep continuation DOI/URL paragraphs unnumbered;
- require no manual Word repair.

If a strategy passes:
1. update the synthetic fixture numbering implementation to use it;
2. add/adjust golden tests;
3. rerun full `pytest -q`;
4. rerun golden Word validation;
5. do not modify unrelated modules.

If no strategy passes:
- do not fake PASS;
- return BLOCKED with exact structural evidence.

## Other rules already added

Do not regress these:
- final section headings are English only;
- section order comes from config;
- article order inside each section comes from Excel;
- section-title cells in TOC/table are centered horizontally and vertically;
- bibliography heading normalization:
  - Ukrainian -> `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ`
  - English -> `REFERENCES`
  - recognize misspellings such as `REFERENS`;
- author/supervisor/affiliation/caption roles remain separate;
- do not globally mutate Normal;
- Word reopen stability remains release-blocking.

## Return JSON only

{
  "task": "astra_numbering_fix",
  "status": "ok|fail|blocked",
  "synced_head": "...",
  "pytest_before": {
    "passed": 0,
    "failed": 0
  },
  "candidates": {
    "A": {
      "roundtrip1_list_values": [],
      "roundtrip2_list_values": [],
      "pass": false,
      "notes": []
    },
    "B": {},
    "C": {},
    "D": {}
  },
  "winning_strategy": "A|B|C|D|null",
  "source_code_updated": true,
  "pytest_after": {
    "passed": 0,
    "failed": 0
  },
  "final_word_roundtrip": "PASS|FAIL|BLOCKED",
  "warnings": [],
  "failures": []
}
