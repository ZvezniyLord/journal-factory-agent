# HERMES_153_INTAKE_CONTINUE.md

## Purpose

Continue the conference 153 real-intake task after the previous Hermes session exhausted its iteration budget before returning the required final JSON.

## Important

Do NOT restart the whole task from zero unless a required artifact is missing or invalid.

Sync the latest branch first:

- repository: `ZvezniyLord/journal-factory-agent`
- branch: `astra/056-clean-room-skeleton`

The branch must contain at least:

`dfcaf9f0cc1f3c7093491364bed4a4505807228a`

This remote branch now includes the useful fixes discovered during the interrupted run:
- ignore year-like values such as 2026 when resolving conference number;
- safe JSON serialization for Excel report values;
- recognize `ім'я` / `имя` as participant-name headers;
- skip blank Excel template-tail rows;
- mark repeated title+section rows as COAUTHOR instead of duplicate publication material.

## Existing local run

Use and validate:

`runs/153_real_intake/`

Expected previously created artifacts may include:
- `inventory.json`
- `excel.json`
- `source_index.json`
- converted legacy DOCX working copies
- `manifest.json` if it was reached.

Do not trust any artifact blindly. Check that its generating code matches the synced branch and regenerate only the artifact affected by a code change.

## Resume sequence

1. Sync latest branch.
2. Run full `pytest -q`.
3. Verify source archive hash has not changed.
4. Confirm `inventory.json` and conference number 153.
5. Regenerate `excel.json` using the synced Excel inspector.
6. Reuse or regenerate converted legacy DOC working copies under the run directory only.
7. Regenerate `source_index.json`.
8. Regenerate `manifest.json`.
9. Inspect manifest summary and all REVIEW/UNMATCHED rows.
10. Complete semantic audit for every matched publication material.
11. Write:
   - `semantic_audit.json`
   - `ambiguities.md`
12. Return the final JSON required by `HERMES_153_INTAKE_TASK.md`.

## Semantic audit must include

For each matched material:
- source file;
- Excel row(s);
- primary author and coauthors;
- UDC/УДК present/missing;
- AUTHOR;
- SUPERVISOR;
- AFFILIATION;
- POSITION_DEGREE;
- ORCID;
- TITLE;
- ABSTRACT;
- KEYWORDS;
- TABLE_CAPTION occurrences;
- FIGURE_CAPTION occurrences;
- REF_TITLE and normalization need;
- reference-region presence;
- raw Excel section;
- section mapping status.

Do not mutate article content.

## Rules

- title-first matching remains primary;
- repeated title+section participant rows are coauthors, not duplicate materials;
- free listeners are not publication materials;
- blank template rows are not participants;
- final section names are English only, but do not invent unapproved mappings;
- missing UDC is a follow-up issue;
- e-mail absence is intentional;
- do not modify persistent Hermes skills;
- do not write to N:;
- do not create final journal yet.

## Return

Return only the JSON schema from `HERMES_153_INTAKE_TASK.md`.
