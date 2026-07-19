# Next Chat Instruction — LLM Core

Open `AGENTS.md` and follow its mandatory navigation exactly.

Read completely:
- `CORE_WORK_REGISTRY.yaml`
- `docs/CORE_DEVELOPMENT_PROTOCOL.md`
- `docs/NEW_CHAT_START.md`
- `docs/BUSINESS_LOGIC_AND_ROADMAP.md`
- `CODEX_INSTRUCTION.md`
- `skills/repository_acceptance/SKILL.md`
- `cores/llm_core/CORE.md`
- `cores/llm_core/DEVELOPMENT_PLAN.md`

Your assigned work item is `llm_core`.

Verify that `llm_core` has no active owner. Claim only this core through `CORE_WORK_REGISTRY.yaml`, commit and push the claim, fetch `origin/main`, and verify that your session is the remote owner before changing implementation or tests.

Work in the user's actual local repository. Synchronize it safely with `origin/main`. Preserve unrelated user changes. Do not use `reset --hard` and do not silently stash user work.

## Goal

Begin test-first implementation of a separate local LLM Core for Journal Factory.

The core must own:
- structured task request and response contracts;
- model/runtime configuration;
- local Ollama adapter;
- prompt templates and versions;
- strict output schema validation;
- confidence and uncertainty fields;
- bounded retries and timeouts;
- typed failures;
- provenance and audit data;
- health/status reporting.

No other core may call Ollama directly, load model weights, hide prompts, or accept unvalidated free-form output as a successful response.

## First development cycle

Implement one narrow end-to-end structured reasoning workflow using explicit ports and adapters.

The request must contain task ID, task type, evidence, constraints, required response schema, confidence requirements, model/runtime options, run ID, and correlation ID.

The response must contain task ID, structured result, confidence, uncertainties, validation state, model identity, runtime information, prompt version, attempt count, timing, provenance, warnings, or a typed failure.

Inspect the actual local Ollama environment. Detect whether Ollama is running and which models are already available. Do not download models or change global Ollama settings without explicit user approval.

Create deterministic test adapters so the core remains testable when Ollama or the required model is unavailable.

## Required tests

Use red-green-refactor and cover:
- request validation;
- response schema validation;
- malformed model output;
- missing required fields;
- confidence threshold failures;
- retryable and non-retryable failures;
- timeout;
- unavailable runtime or model;
- adapter exception suppression;
- attempt counting;
- provenance;
- prompt versioning;
- deterministic JSON serialization;
- no free-form success path;
- loopback-only binding if an HTTP adapter is added.

Run focused tests, the full available suite, compile checks, deterministic real run, local Ollama smoke test when possible, architecture review, forbidden-import review, and repository acceptance.

Do not implement document parsing, Excel processing, UDC logic, browser UI, Dashboard internals, Orchestrator internals, embeddings, model training, or automatic model downloading.

After verification, update the LLM Core passport and development plan, commit and push the implementation, record `last_result` and `last_commit`, release only the `llm_core` lock, push the release, fetch again, and verify `in_progress: false`.

Finish with:

`STATUS: LLM CORE CYCLE COMPLETE`

or

`STATUS: BLOCKED — <exact reason>`
