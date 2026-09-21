# LAUNCH_PROMPT.md

Work only inside the current `Codex_6/056_Astra` workspace.

This is a clean-room rebuild. Do not inspect, import, grep, open or reuse code/configuration from parent directories, sibling projects, old scripts, old skills or previous implementations.

Authoritative local instructions:
1. `ASTRA_MASTER.md`
2. `EDITORIAL_RULES.md`
3. `HERMES_PROTOCOL.md`
4. `SKILL_INTEGRATION.md`
5. `naukainfo.yaml`
6. `config/hermes_runtime.json`

## Mandatory startup sequence

Do this **before finalizing your architecture plan and before production implementation**:

1. Read the six local instruction/config files above.
2. Create `runs/bootstrap/`.
3. Read `config/hermes_runtime.json`.
4. Connect to the configured main Hermes OpenAI-compatible endpoint.
5. Verify model discovery.
6. Send the real strict-JSON bootstrap healthcheck from `HERMES_PROTOCOL.md`.
7. Save the actual result as `runs/bootstrap/hermes_handshake.json`.
8. If main fails, try the configured fallback worker.
9. If both fail, stop with `BLOCKED_HERMES_BOOTSTRAP`; do not silently proceed without Hermes.
10. Draft a short architecture/implementation plan.
11. Send only that compact plan to Hermes using `review_astra_plan`.
12. Save the response as `runs/bootstrap/hermes_plan_review.json`.
13. Improve the plan where Hermes found valid gaps, but keep Astra as final decision-maker.
14. Write `ARCHITECTURE.md` and `IMPLEMENTATION_PLAN.md` with a short record of accepted/rejected Hermes suggestions.

The first real Hermes request should warm/load the local model automatically through Ollama.

## Development behavior

Use Hermes as a semantic subagent throughout development and runtime for noisy archive scanning, classification, source matching, header interpretation, duplicate/version analysis, section classification and bibliography-continuation ambiguity.

Do not spend Astra context manually reading hundreds of complete source documents. Extract compact evidence, delegate bounded semantic tasks to Hermes, validate strict JSON, save responses to disk, and continue from manifests.

Hermes must NOT edit DOCX, numbering, styles, relationships or TOC and must not issue final QA verdicts.

After Hermes bootstrap and plan review:

- implement `path_guard`;
- create typed schemas;
- implement the production Hermes adapter/cache;
- implement a minimal DOCX inspector;
- create and pass the blocking golden tests from `ASTRA_MASTER.md`;
- only then build the full journal pipeline.

Do NOT begin with one monolithic script.

Keep active context compact:
- no whole archives/journals;
- no huge XML dumps;
- stage-by-stage processing;
- state on disk;
- compact JSON/manifest handoffs.

Do not report completion until:
- a real final `journal.docx` exists;
- all required participants/materials are accounted for;
- front matter is unchanged;
- content/formatting/object/reference/TOC QA passes;
- every bibliography restarts at 1 as a real Word list;
- Word/render QA is complete;
- final status is `PASS` or explicitly `PASS_WITH_WARNINGS`.

If a blocking invariant cannot be satisfied, return `BLOCKED` with the exact reason. Do not silently repair scientific content or invent missing data.
