# CURRENT_STATUS.md

## Current stage

Astra 056 is not yet a production journal builder. It is at the end of foundation hardening / beginning of blocking golden-test work.

### Completed and locally validated
- clean-room path guard;
- safe ZIP extraction guard;
- real Hermes MAIN handshake;
- Hermes main/fallback router;
- strict Hermes envelope validation;
- deterministic Hermes disk cache;
- workspace-local virtual environment bootstrap;
- local sync provenance;
- 11 foundation tests passed on the operator PC;
- explicit Word COM final-release policy;
- explicit REFER numbering strategy in config;
- DOCX style/reopen-risk inspector;
- detection of autoRedefine, theme-font dependencies and inconsistent footer distances;
- safe style-hardening primitive that refuses global Normal mutation.

### New production incident incorporated
A real conference journal demonstrated save/close/reopen formatting drift caused by mixed style inheritance, autoRedefine and theme-font fallbacks. This is now a release-blocking Word-stability requirement.

### Not completed
- golden DOCX fixture generators;
- Excel registry parser;
- DOC/DOCX forensic extractor;
- article/questionnaire/source matcher;
- production role classifier;
- canonical article normalization;
- reference engine;
- OOXML multi-article merge engine;
- TOC builder;
- content/object/format integrity engine;
- Word COM roundtrip + visual comparison integration;
- full journal CLI;
- real archive -> final journal end-to-end run.

## Next blocking milestone

Do not attempt a real archive-to-journal release yet.

Next:
1. sync newest branch to local 056_Asttra;
2. run all tests;
3. validate Word COM roundtrip helper on the repaired conference 153 journal or a copy;
4. build synthetic golden fixtures;
5. implement intake + Excel + DOCX inspector;
6. only then expose astra-journal build.

Hermes remains semantic subagent. Deterministic Python/OOXML code remains mutation authority.
