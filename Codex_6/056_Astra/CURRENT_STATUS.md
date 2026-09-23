# CURRENT_STATUS.md

## Current stage

Astra 056 is not yet a complete production journal builder. Foundation hardening and the first blocking golden/Word tests are now passing; implementation has moved into production intake and manifest construction.

### Completed and locally validated
- clean-room path guard;
- safe ZIP extraction guard;
- real Hermes MAIN handshake;
- Hermes main/fallback router;
- strict Hermes envelope validation;
- deterministic Hermes disk cache;
- workspace-local virtual environment bootstrap;
- local sync provenance;
- foundation test suite passed on the operator PC;
- Word-stable REFERENCES restart strategy B validated after two consecutive Word COM roundtrips;
- explicit Word COM final-release policy;
- explicit REFER numbering strategy in config;
- DOCX style/reopen-risk inspector;
- detection of autoRedefine, theme-font dependencies and inconsistent footer distances;
- safe style-hardening primitive that refuses global Normal mutation.

### New production incident incorporated
A real conference journal demonstrated save/close/reopen formatting drift caused by mixed style inheritance, autoRedefine and theme-font fallbacks. This is now a release-blocking Word-stability requirement.

### Implemented / in progress
- synthetic golden DOCX fixture;
- Excel registry inspector;
- DOCX forensic inspector;
- title-first article matcher;
- production archive intake/inventory;
- production run/destination model;
- deterministic paragraph-role classifier.

### Not completed
- legacy DOC conversion in production intake;
- full manifest builder across Excel + sources + questionnaires;
- production role classifier integration;
- canonical article normalization;
- reference engine;
- OOXML multi-article merge engine;
- TOC builder;
- content/object/format integrity engine;
- Word COM roundtrip + visual comparison integration;
- full journal CLI;
- real archive -> final journal end-to-end run.

## Next blocking milestone

Do not attempt a final archive-to-journal release yet.

Next:
1. sync newest branch to local 056_Asttra;
2. run all tests;
3. run production intake on the real conference 153 archive;
4. identify the Excel registry and all article/questionnaire candidates;
5. build title-first matches and ambiguity report;
6. integrate role classification, missing-UDC detection and section mapping;
7. then implement normalization/merge/TOC and expose astra-journal build.

Hermes remains semantic subagent. Deterministic Python/OOXML code remains mutation authority.


## Stateless semantic-audit architecture

Long interactive Hermes sessions on the real conference 153 intake repeatedly reached large pinned contexts and provider instability. Production semantics has therefore been moved out of accumulated controller-chat context.

Implemented:
- bounded semantic signals extracted deterministically from each DOCX;
- one article per direct OpenAI-compatible Hermes request;
- no previous article messages carried into the next request;
- hard request/output limits;
- sequential requests only;
- strict article-semantic JSON envelope validation;
- disk cache for successful article calls;
- checkpoint after every article;
- resumable micro-batches of at most 3 new article requests per controller process;
- compact controller output only;
- full per-article responses remain on disk;
- provider failure does not require restarting completed articles.

Real validation task:
`HERMES_153_STATELESS_TEST.md`
