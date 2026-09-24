# HERMES_153_PILOT_BUILD_TASK

Goal: implement the first deterministic pilot journal builder for conference 153.

This is a pilot only. Do not write to N:.

Workspace mirror:
X:\CODEX_5.5_redactor\Codex_6\056_Asttra

Git repo:
X:\CODEX_6\journal-factory-agent

Use existing run data:
runs/153_real_intake/

## First
1. Sync branch astra/056-clean-room-skeleton.
2. Run pytest -q.
3. Do not rerun archive intake unless an input is missing.

## Implement
Add deterministic CLI command:

astra-journal build-pilot

Target invocation:

.venv\Scripts\python.exe -m astra_journal.cli build-pilot --run-dir runs\153_real_intake --output runs\153_pilot_build\153-pilot.docx

Use manifest.json, source_index.json, semantic_audit.json and source DOCX working copies.

Hermes is advisory only. Python/OOXML/Word COM performs all document mutations.

## Required behavior
- one material per publication; free listeners create no articles; coauthors create no duplicate articles;
- article order inside sections follows Excel;
- section headings in final journal are English only and come from approved/configured mapping;
- article top order: UDC -> author header -> title -> abstract/keywords when present -> body -> bibliography;
- preserve text and local bold/italic/underline/superscript/subscript;
- preserve tables, images, hyperlinks, formulas/OOXML objects and relationships;
- remove author e-mails from publication output;
- institution is not an author;
- supervisor is not a coauthor unless explicitly an author;
- normalize bibliography heading by article language;
- use validated REFERENCES numbering Strategy B so every article restarts at 1 and DOI/URL continuations are unnumbered;
- do not globally mutate Normal;
- canonical body target: Times New Roman 11 pt, justified, single spacing, 0 pt after, first-line indent 1 cm;
- preserve protected front matter before TABLE OF CONTENTS;
- build TOC from actual merged structure.

## Pilot QA
Block success unless checked:
- material completeness / no duplicates;
- text integrity against sources;
- local formatting integrity;
- table/image/hyperlink/media integrity;
- reference numbering restart and no numbering leakage;
- section and article order;
- no e-mails;
- Word COM SaveAs2 -> close -> reopen;
- second Word roundtrip;
- post-roundtrip style/content audit.

Create:
runs/153_pilot_build/153-pilot.docx
runs/153_pilot_build/build_manifest.json
runs/153_pilot_build/qa_report.json
runs/153_pilot_build/word_roundtrip_1.json
runs/153_pilot_build/word_roundtrip_2.json
runs/153_pilot_build/ambiguities.md

Unresolved UDC or unapproved section mapping must be explicit QA issues; do not invent data.

## Development rules
- add tests for new modules;
- do not mutate source files;
- do not inspect unrelated legacy repos;
- do not create/modify persistent Hermes skills;
- do not manually patch final Word file;
- keep controller output compact.

## Finish
After implementation:
1. run full pytest;
2. run the pilot build if inputs permit;
3. git status;
4. commit all relevant source/test/config/task changes;
5. push to the same branch;
6. do not merge PR.

Return only:
- synced HEAD before work;
- pytest before/after;
- files added/changed;
- pilot-build result;
- QA summary;
- new commit SHA;
- pushed HEAD SHA;
- blockers/warnings.
