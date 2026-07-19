# AGENTS.md — Journal Factory

## Mandatory navigation for every new agent chat

This file is the starting point and reading router for the repository.

Do not rely on chat memory, a copied prompt, prior success messages, or commit titles. Repository documents are the persistent source of truth.

Follow this sequence exactly:

1. Read this `AGENTS.md` completely.
2. Open and read `CORE_WORK_REGISTRY.yaml` completely.
3. Return to this file.
4. Resolve the user's requested work to exactly one registered core or coordination-only task.
5. Check that core's `in_progress` value, current phase, dependencies, development case, passport path, development-plan path, and allowed write scope.
6. Open and read `docs/CORE_DEVELOPMENT_PROTOCOL.md` completely.
7. Return to this file.
8. Open and read `docs/NEW_CHAT_START.md` completely.
9. Return to this file.
10. Open and read `docs/BUSINESS_LOGIC_AND_ROADMAP.md` completely, including the selected core and its dependencies.
11. Return to this file.
12. Open and read `CODEX_INSTRUCTION.md` completely.
13. Return to this file.
14. Open and read `skills/repository_acceptance/SKILL.md` completely.
15. Return to this file.
16. Perform the repository acceptance audit before modifying code.
17. Verify that the selected core has both `cores/<core_id>/CORE.md` and `cores/<core_id>/DEVELOPMENT_PLAN.md`; create and register them before implementation if missing.
18. Claim the selected core through `CORE_WORK_REGISTRY.yaml`, commit the claim, push it, fetch again, and verify remote ownership before modifying any implementation, test, fixture, API, UI, passport, plan, or core-specific documentation file.
19. Begin only the currently approved development cycle.

No referenced document may be replaced by a summary. Do not skip ahead.

## Core work coordination — mandatory write lock

`CORE_WORK_REGISTRY.yaml` is the machine-readable coordination source of truth for all agent chats. `docs/CORE_DEVELOPMENT_PROTOCOL.md` is the mandatory detailed procedure.

Every user phrase such as `Працюй над УДК`, `work on UDC`, or `ядро УДК` must be resolved through `selection_aliases` to the registered core `udc_detection`. The agent must then read that core's complete record, passport, and development plan to understand its exact development case, dependencies, phase, acceptance outline, status, current progress, and next action.

Rules:

- Everyone may read every core at any time.
- No agent may modify a core or its write scope while that core has `in_progress: true` and belongs to another session.
- `in_progress: false` means the core is available, not automatically approved for the current phase.
- Before implementation, the agent must fetch current `origin/main`, reread the registry, set `in_progress: true`, fill all lock metadata, commit the claim as a separate commit, push it, fetch again, and verify that current remote main still names the same session as owner.
- The lock must identify `lock_owner`, a unique `lock_session`, `claimed_at_utc`, `branch`, `work_item`, and exact non-overlapping `allowed_write_scope`.
- Claiming the registry locally, stating in chat that work started, or creating an unpushed commit does not acquire the lock.
- Implementation work starts only after the pushed lock is visible and verified on current `origin/main`.
- If two claims conflict, the agent that cannot prove ownership on current `origin/main` must stop with `BLOCKED`.
- An agent must not clear another agent's lock merely because it appears old. Only the lock owner or explicit user authorization may release or recover it.
- After tests, real run, artifact inspection, architecture review, repository acceptance, and final reporting, the owner must push the implementation, return to the registry, record the result and implementation commit, set `in_progress: false`, clear the active lock fields, commit the release separately, push it, fetch again, and verify the release remotely.
- Work is not closed until `in_progress: false` is visible on current `origin/main`.
- If the chat is interrupted, the agent must record `blocked` or `interrupted`; it must never leave an unexplained lock state.
- A locked core may still be inspected, discussed, or reviewed read-only. Its implementation, tests, fixtures, API contracts, UI behavior, passport, development plan, and core-specific documentation must not be changed by another session.
- Two chats may work simultaneously only on different registered cores with disjoint write scopes.
- Shared files must be changed only after a fresh fetch, explicit ownership check, the smallest possible edit, separate commit and push, and remote verification. A stale local copy must never overwrite a shared file.
- If requested work names a missing core, first register it with `in_progress: false`, aliases, phase, dependencies, passport path, development-plan path, and write scope; commit and push that registration; fetch and verify it; only then acquire its lock.

The boolean is the required human-visible signal:

```yaml
in_progress: true   # a verified owner is actively working
in_progress: false  # no active owner
```

The associated metadata and the commit/push/fetch verification are mandatory because a boolean alone cannot safely distinguish competing chats.

## Mandatory passport and detailed development plan

Every core must have:

```text
cores/<core_id>/CORE.md
cores/<core_id>/DEVELOPMENT_PLAN.md
```

`CORE.md` is the permanent passport and defines identity, aliases, business purpose, exact boundaries, exclusions, inputs, outputs, ports, adapters, interfaces, typed errors, dependencies, consumers, state ownership, deterministic rules, permitted LLM escalation, reports, provenance, security, acceptance criteria, limitations, and future extensions.

`DEVELOPMENT_PLAN.md` is the core-specific executable plan derived from all repository documents, drafts, prior work, tests, and accepted decisions. It defines baseline evidence, assumptions, architecture, module layout, staged cycles, failing tests, positive and negative cases, boundary and recovery cases, integration tests, fixtures, real-run samples, risks, observability, manual testing, completion criteria, completed work, current state, next exact action, and blockers.

A generic copied plan is forbidden. The passport and plan must be updated as the core evolves.

## Separate principal cores

These are separate cores and must never be collapsed:

- **Orchestrator Core** — deterministic conductor for registration, dependency checks, routing, state transitions, invocation contracts, retries, pause/resume, failure routing, and action logging. It does not implement another core's domain logic.
- **Dashboard Core** — the operational execution center exposed through the browser. It receives paths and run parameters, starts or restores runs, requests work through explicit ports, tracks all cores, and presents progress, warnings, reports, files, and final results. It does not contain Excel parsing, matching, DOCX transformation, UDC detection, or LLM reasoning.
- **LLM Core** — a separate callable reasoning service. Other cores submit structured tasks, evidence, constraints, required response schemas, and confidence requirements. Model weights, runtime adapter, prompts, validation, retries, provenance, and structured responses belong only to this core. No other core may embed or invoke model weights directly.

HTML is an adapter and presentation layer. Business logic must not live in HTML.

## Document responsibilities

- `CORE_WORK_REGISTRY.yaml` — core catalog, aliases, current phase, development cases, dependencies, passport and development-plan paths, write locks, owners, work status, and results.
- `docs/CORE_DEVELOPMENT_PROTOCOL.md` — mandatory core architecture separation, passport and plan requirements, missing-core registration, exact claim/push/verify and release/push/verify lifecycle, and parallel-agent conflict prevention.
- `docs/NEW_CHAT_START.md` — canonical startup protocol for a fresh Codex/Sol chat, current cycle order, testing, real-run, user-testing, and reporting rules.
- `docs/BUSINESS_LOGIC_AND_ROADMAP.md` — complete product business logic, all cores, system workflow, quality rules, and long-term roadmap.
- `CODEX_INSTRUCTION.md` — technical implementation contract, cleanup rules, current classes, APIs, tests, and phase gates.
- `skills/repository_acceptance/SKILL.md` — mandatory independent verification after every cleanup, cycle, migration, or implementation stage.

When documents appear to conflict, stop with `BLOCKED`, quote the conflicting requirements, and request resolution. Do not silently choose one.

## Product purpose

Journal Factory is a local, browser-driven system for discovering conference source files, matching Excel registry records to article documents, transforming each article independently, assembling the final journal, rendering it, and validating the result.

The architecture must follow OOP, SOLID, dependency inversion, explicit ports and adapters, typed errors, deterministic core logic, and test-first development. A monolithic linear script is forbidden.

## Non-negotiable universal document invariant

After the dashboard and workspace are created, the first document-editing operation is universal normalization.

Every editable text element in every transformed article and assembled journal must use:

- font size: **11 pt**;
- line spacing: **1.0 / single**.

This applies without exception to body text, article headers, authors, affiliations, UDC, titles, annotations, keywords, headings, table cells, captions, figure labels stored as editable text, references, bibliography entries, headers, footers, notes, and service text.

Rasterized text inside an image cannot be reformatted, but its caption and every editable surrounding object must follow the rule. Any editable production text violating 11 pt or 1.0 is a hard `FAIL`.

## Single human entry point

The root `index.html`, served by a local backend on `127.0.0.1`, is the only normal human-facing entry point.

The browser interface must eventually allow the operator to:

- select the source folder;
- select the output parent;
- use a Desktop default named by journal/conference number;
- review the journal number;
- start, inspect, pause where supported, and resume the pipeline;
- inspect every core, article, warning, LLM call, match score, report, and final quality gate.

Business logic must not live in HTML.

## Core architecture summary

The detailed contracts live in `docs/BUSINESS_LOGIC_AND_ROADMAP.md`. The coordination and lock state live in `CORE_WORK_REGISTRY.yaml`. The mandatory per-core engineering and multi-agent procedure lives in `docs/CORE_DEVELOPMENT_PROTOCOL.md`.

Approved cores include:

1. Workspace Driver Core
2. Browser UI Core
3. Source Discovery Core
4. Source Snapshot Core
5. Excel Registry Core
6. Retrieval and Matching Core
7. Article Processing Coordinator
8. Marker Knowledge Core
9. Article Segmentation Core
10. Header Core
11. Document Normalization Core
12. Table Core
13. Figure Core
14. Reference Core
15. Assembly Core
16. Rendering Core
17. QA Core
18. Reporting and Dashboard Core
19. Orchestrator Core
20. LLM Core
21. Focused capabilities registered as explicit work units, including UDC Detection Core

Each core must expose an explicit interface and machine-readable reports. Deterministic Python logic is primary. Ambiguous reasoning must be delegated through the separate LLM Core using a logged structured request/response contract.

## Workspace authority

`WorkspaceDriver` and its class family own only:

- source and output paths;
- run identity;
- journal number;
- canonical directory creation;
- path registry;
- run context;
- action history;
- report registry;
- persisted run state.

Required abstractions:

- `WorkspaceConfig`
- `WorkspaceLayout`
- `RunContext`
- `ActionRecord`
- `ReportRecord`
- `PathRegistry`
- `ReportRegistry`
- `WorkspaceDriverPort`
- `WorkspaceDriver`
- `FileSystemAdapter`

All other cores receive paths through `WorkspaceDriverPort`. They must not construct ad-hoc absolute workspace paths.

Canonical workspace directories:

```text
source_snapshot/
articles_raw/
articles_transformed/
reports/
logs/
database/
rendered/pdf/
rendered/png/
final/
temp/
```

Required persisted reports:

- `reports/run_manifest.json`
- `reports/action_log.jsonl`
- `reports/path_registry.json`
- `reports/report_registry.json`
- `reports/run_summary.html`

## Current approved scope

The current approved scope is **Phase 1 only**.

Phase 1 includes:

- root `index.html`;
- local backend and launcher;
- source-folder selection or bridge;
- output-parent selection or bridge;
- journal number;
- Desktop default;
- computed workspace path;
- Workspace Driver class family;
- defaults, validate, create, and status APIs;
- canonical workspace creation;
- deterministic JSON/JSONL reports;
- automated tests;
- real launch and user manual testing.

Do not implement before Phase 1 is accepted:

- Excel parsing;
- DOC/DOCX parsing or editing;
- Header Core;
- marker detection, including UDC detection;
- article transformation;
- retrieval/RAG;
- embeddings;
- local LLM integration or model weights;
- journal assembly;
- document formatting implementation;
- PDF/PNG rendering;
- production document QA.

A user request naming a future core identifies the intended work unit but does not override the phase gate. The agent must report `BLOCKED` or request explicit phase approval rather than secretly implementing it.

The detailed Phase 1 cycles and fresh-chat first action are defined in `docs/NEW_CHAT_START.md` and `CODEX_INSTRUCTION.md`.

## Mandatory development loop

Every cycle uses:

`READ -> REGISTER IF MISSING -> CREATE/UPDATE PASSPORT -> CREATE/UPDATE DETAILED PLAN -> CLAIM CORE -> COMMIT CLAIM -> PUSH CLAIM -> FETCH AND VERIFY OWNER -> FAILING TEST -> MINIMAL IMPLEMENTATION -> FOCUSED TEST -> FULL TEST SUITE -> REAL RUN -> ARTIFACT INSPECTION -> ARCHITECTURE REVIEW -> REPOSITORY ACCEPTANCE -> PUSH IMPLEMENTATION -> RECORD RESULT -> RELEASE CORE -> COMMIT RELEASE -> PUSH RELEASE -> FETCH AND VERIFY FREE -> FIX/REPEAT`

After every cycle apply `skills/repository_acceptance/SKILL.md`.

Never proceed while status is `BLOCKED`.

After every externally visible cycle, provide exact manual-test instructions and stop with `STATUS: WAITING FOR USER` until the user reports the result. The core may remain locked while genuinely waiting for that user's test, but the registry must state this explicitly in `status`, `work_item`, and `notes`. It must be released after the accepted cycle is closed or the user directs the agent to stop.

## Output quality gate

Production output is not ready unless the final quality report explicitly marks it ready.

Allowed final states:

- `PASS`
- `PASS WITH WARNINGS`
- `FAIL`

A draft DOCX must never be presented as final without the quality gate.

## First instruction to a fresh Codex/Sol chat

The only message normally needed from the user is:

```text
Open AGENTS.md in the repository and follow its mandatory navigation exactly. Resolve my requested work through CORE_WORK_REGISTRY.yaml, read the core passport and detailed development plan, acquire and remotely verify the pushed core lock before writing, start only an approved cycle, perform all tests and real-run checks, give me the manual test, then record the result, release the lock, push the release, and verify on origin/main that the core is free.
```

For a named core, the user may write simply:

```text
Open AGENTS.md and work on УДК.
```

The agent must resolve `УДК` through the registry, inspect its development case and phase, read its passport and plan, and either acquire the correct remotely verified lock or stop with an exact `BLOCKED` reason.

Everything else must be loaded from the repository documents.
