# LAUNCH_PROMPT.md

Work only inside the current `Codex_6/056_Astra` workspace.

This is a clean-room rebuild. Do not inspect, import, grep, open or reuse code/configuration from parent directories, sibling projects, old scripts, old skills or previous implementations.

Authoritative local instructions:
1. `ASTRA_MASTER.md`
2. `EDITORIAL_RULES.md`
3. `HERMES_PROTOCOL.md`
4. `naukainfo.yaml`

First:
- read those four files;
- create a concise `ARCHITECTURE.md`;
- create typed schemas;
- implement the path boundary;
- implement the Hermes adapter contract;
- implement a minimal DOCX inspector;
- create and pass the blocking golden tests listed in `ASTRA_MASTER.md`.

Do NOT begin by writing a monolithic full journal pipeline.

Use Hermes actively for noisy archive/document semantic scanning, classification, matching and ambiguous header/reference interpretation. Do not let Hermes edit DOCX, numbering, styles, TOC or issue final QA verdicts.

Keep model context compact:
- do not load whole archives/journals into context;
- process stage-by-stage;
- persist manifests, Hermes JSON, audits and run state to disk;
- continue from compact structured files.

After golden tests pass, implement the complete deterministic journal factory and run an end-to-end build on the explicitly supplied inputs.

Do not report completion until:
- a real final `journal.docx` exists;
- all required participants/materials are accounted for;
- front matter is unchanged;
- content/formatting/object/reference/TOC QA passes;
- every bibliography restarts at 1 as a real Word list;
- Word/render QA has been completed;
- final status is `PASS` or explicitly `PASS_WITH_WARNINGS`.

If a blocking invariant cannot be satisfied, return `BLOCKED` with the exact reason. Do not silently repair scientific content or invent missing data.
