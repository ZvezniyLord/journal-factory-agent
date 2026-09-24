# HERMES_153_INTAKE_TASK.md

## Goal

Run the first real production-intake test on conference 153 using Astra. This is NOT yet a final journal build.

## Archive

`E:\Downloads\38833FF26BA1D.UnigramPreview_g9c9v27vpyspw!App\153_м_Харків,_Україна,_3 5_вересня_2026_року.rar`

## Local workspace

`X:\CODEX_5.5_redactor\Codex_6\056_Asttra`

## Required first step

Sync the latest branch:

- repository: `ZvezniyLord/journal-factory-agent`
- branch: `astra/056-clean-room-skeleton`

The synced branch must contain at least commit:

`671b681e3732de5552e8d9110754b62123f0a9c8`

Do not require exact HEAD equality if newer commits exist.

Then run the full local test suite before touching the archive.

## Intake run

Create:

`runs/153_real_intake/`

Run:

`.venv\Scripts\python.exe -m astra_journal.cli intake-archive "<ARCHIVE>" --run-dir runs\153_real_intake --json runs\153_real_intake\inventory.json`

Confirm:
- conference_number = 153;
- source archive remains unchanged;
- extraction occurs only into the run workspace;
- Excel candidates are identified;
- DOC/DOCX candidates are identified;
- questionnaires/applications are separated when recognizable;
- templates are identified if present.

## Legacy .doc handling

If the source index reports legacy .doc files:
- convert only working copies with `astra-journal convert-doc`;
- save converted files under `runs/153_real_intake/converted/`;
- never alter the originals;
- verify the converted DOCX opens and contains non-empty text.

## Excel registry

Choose the actual participant registry using evidence from headers/content, not filename alone.

Run:

`astra-journal inspect-excel <registry.xlsx> --json runs\153_real_intake\excel.json`

Report:
- sheet name;
- participant row count;
- detected title column;
- detected author column;
- detected section column;
- free-listener field if present;
- DOI / printed-copy fields if present;
- any unmapped important columns.

Do not reinterpret Excel business data through general knowledge.

## Source index

Run:

`astra-journal source-index <extracted-or-converted-root> --json runs\153_real_intake\source_index.json`

Do not load full articles into chat context. Work from compact JSON.

For ambiguous title candidates, Hermes may inspect only the relevant compact excerpt.

## Manifest

Run:

`astra-journal build-manifest runs\153_real_intake\excel.json runs\153_real_intake\source_index.json --json runs\153_real_intake\manifest.json`

The primary matching rule is TITLE, not author surname.

For each required material:
- matched exactly once;
- free listeners are not assigned fabricated articles;
- coauthors do not create duplicate materials;
- unused DOC/DOCX files are listed;
- low-confidence title matches remain REVIEW.

## Semantic audit for next implementation stage

Using only compact source excerpts + manifest, identify for each matched article:

- likely UDC/УДК line and whether it is missing;
- AUTHOR;
- SUPERVISOR;
- AFFILIATION;
- POSITION_DEGREE;
- ORCID;
- TITLE;
- ABSTRACT;
- KEYWORDS;
- TABLE_CAPTION;
- FIGURE_CAPTION;
- REF_TITLE;
- likely REFERENCE region;
- section from Excel and proposed canonical English section mapping.

Do not mutate article files in this task.

Important rules:
- canonical top order will be UDC -> author header -> title -> article content;
- final section headings are English only;
- article order inside sections follows Excel;
- institution is never an author;
- supervisor is not a coauthor unless explicitly an author;
- missing UDC is a required follow-up item;
- bibliography headings normalize to:
  - Ukrainian: `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ`
  - English: `REFERENCES`;
- table/figure captions must be recognized separately from body text;
- e-mail absence is intentional and must not be treated as text loss.

## Do not do yet

- do not build the final conference journal;
- do not mutate original source files;
- do not write anything to drive N:;
- do not invent canonical English section names that are not configured/approved;
- do not modify persistent Hermes self-improvement skills;
- do not inspect parent/sibling legacy code;
- do not summarize the entire archive into chat context.

## Required artifacts

Under `runs/153_real_intake/` produce at least:

- `inventory.json`
- `excel.json`
- `source_index.json`
- `manifest.json`
- `semantic_audit.json`
- `ambiguities.md`

## Return JSON only

{
  "task": "astra_153_real_intake",
  "status": "ok|fail|blocked",
  "synced_head": "...",
  "pytest": {"passed": 0, "failed": 0},
  "conference_number": "153",
  "registry": {
    "path": "...",
    "rows": 0,
    "detected_columns": {}
  },
  "sources": {
    "docx": 0,
    "legacy_doc": 0,
    "converted_doc": 0,
    "questionnaires": 0
  },
  "manifest": {
    "matched": 0,
    "review": 0,
    "free_listeners": 0,
    "unused_sources": 0
  },
  "semantic_audit": {
    "missing_udc": 0,
    "author_role_ambiguities": 0,
    "caption_ambiguities": 0,
    "reference_heading_normalizations": 0,
    "section_mapping_review": 0
  },
  "warnings": [],
  "failures": []
}
