# HERMES_PROTOCOL.md
## Local Hermes subagent contract

## 1. Role
Hermes is the local semantic subagent for Astra.

> **Hermes interprets; Astra decides and mutates.**

Hermes is not a DOCX editor and not a release authority.

Astra must connect to Hermes **before architecture planning** for this project, verify the runtime with a real request, and use Hermes to critique the initial plan.

## 2. Validated local runtime profile
Runtime values are stored in `config/hermes_runtime.json`.

Current validated layout:

### Main worker
- OpenAI-compatible base URL: `http://127.0.0.1:11434/v1`
- Model: `qwen3.8-27b-q2-229k-gpu66:latest`
- Context: `229376`
- Purpose: primary Hermes semantic subagent

### Fallback CPU worker
- OpenAI-compatible base URL: `http://127.0.0.1:11435/v1`
- Model: `qwen3.8-27b-q2_k_xl-128k:latest`
- Context: `65536`
- Purpose: fallback/manual helper if main endpoint is unavailable

No secrets are stored in repository config.

## 3. Mandatory bootstrap handshake
Before finalizing the plan:

1. Read `config/hermes_runtime.json`.
2. Query the main endpoint's model list.
3. Send a real chat-completion smoke test using the configured model.
4. Require strict JSON.
5. Save endpoint/model/latency/result to `runs/bootstrap/hermes_handshake.json`.
6. If main fails, repeat against fallback.
7. If both fail, return `BLOCKED_HERMES_BOOTSTRAP`.

The smoke test should be trivial and deterministic, for example:

```json
{
  "task": "bootstrap_healthcheck",
  "instruction": "Return JSON only with status=ok, role=hermes_subagent, arithmetic=42."
}
```

Expected semantic result:

```json
{
  "status": "ok",
  "role": "hermes_subagent",
  "arithmetic": 42
}
```

A valid equivalent envelope is acceptable if schema validation confirms those three values.

The first real inference also serves as model warm-up/load.

## 4. Mandatory plan co-review
After Astra reads the specs and drafts a **compact** plan, send only:
- plan summary;
- constraints;
- major invariants;
- proposed module boundaries;
- proposed golden tests.

Task type: `review_astra_plan`.

Ask Hermes to return strict JSON:

```json
{
  "task": "review_astra_plan",
  "status": "ok",
  "confidence": 0.0,
  "result": {
    "blockers": [],
    "gaps": [],
    "risks": [],
    "missing_tests": [],
    "token_saving_opportunities": [],
    "hermes_delegation_improvements": [],
    "suggested_changes": []
  },
  "evidence": [],
  "warnings": []
}
```

Astra must decide which suggestions to adopt. Hermes does not control the plan.

Save the response to `runs/bootstrap/hermes_plan_review.json`.

## 5. Allowed Hermes tasks
Use Hermes actively for:
- classify noisy archive files;
- article / questionnaire / application / old_version / journal / misc classification;
- probable title extraction;
- probable author extraction;
- supervisor extraction;
- person vs institution separation;
- affiliation extraction;
- probable UDC/DOI detection;
- thematic section suggestion;
- article ↔ questionnaire/source candidate matching;
- duplicate/alternate-version detection;
- bibliography continuation classification;
- ambiguous header-role classification;
- compact review of deterministic transformation results;
- explicitly supplied old journal/article pattern analysis;
- plan/risk critique.

Hermes should handle high-volume semantic reading so Astra does not spend its own context reading hundreds of documents.

## 6. Forbidden Hermes tasks
Hermes MUST NOT:
- directly edit DOCX;
- write `document.xml`;
- choose/create `numId`;
- restart numbering;
- remap styles;
- merge relationships;
- mutate TOC;
- decide final Word formatting;
- rewrite scientific content;
- invent missing metadata;
- silently override Excel/article evidence;
- issue final PASS/BLOCKED verdict.
- create or update persistent agent skills outside the Astra workspace;
- treat self-improvement memories/skills as authoritative project rules.

## 7. Input discipline
Core rule:

`ONE TASK -> SMALL INPUT -> STRICT JSON -> VALIDATE -> CACHE`

Never send:
- entire journal;
- entire archive;
- huge OOXML;
- dozens of full articles in one prompt.

Astra first performs deterministic compact extraction, then delegates only the semantic fragment.

## 8. Configuration and adapter
Runtime is externalized.

The adapter must support:
- OpenAI-compatible `/v1/models`;
- OpenAI-compatible `/v1/chat/completions`;
- main/fallback routing;
- timeout;
- bounded retry;
- strict per-task JSON-schema validation;
- confidence-range validation;
- request-size estimation;
- cache;
- audit IDs.

Retry, fallback, schema validation, caching and audit IDs are deterministic Python responsibilities, never Hermes judgement.

Environment variables may override repository defaults:
```text
HERMES_BASE_URL
HERMES_MODEL
HERMES_CONTEXT
HERMES_FALLBACK_BASE_URL
HERMES_FALLBACK_MODEL
HERMES_FALLBACK_CONTEXT
HERMES_TIMEOUT
HERMES_MAX_OUTPUT
HERMES_BATCH_SIZE
```

## 9. Generic response envelope
For semantic tasks prefer:

```json
{
  "task": "task_name",
  "status": "ok",
  "confidence": 0.0,
  "result": {},
  "evidence": [],
  "warnings": []
}
```

No prose outside JSON.

## 10. Confidence policy
Defaults:
- `>= 0.95`: eligible for automatic acceptance only if deterministic checks also agree;
- `0.80..0.949`: advisory/review;
- `< 0.80`: no auto-accept.

Identity-sensitive cases require stronger deterministic evidence.

## 11. Batching and token economy
Batch only homogeneous compact tasks.

For production **article semantic audit**, batching is forbidden: exactly one article per request.

Good:
- short file names + excerpts;
- compact header candidates;
- short bibliography neighborhoods;
- one bounded article semantic packet.

Bad:
- complete DOCX bodies;
- full journals;
- XML dumps.

Do not use Hermes's large context as an excuse to send oversized inputs. The purpose is to save Astra tokens and keep evidence auditable.

## 11A. Stateless production article calls

For production article semantics, the interactive Hermes chat is **controller-only**.

Do not accumulate article-by-article evidence, tool logs, full responses or semantic results in one Hermes conversation.

Required architecture:

`ONE ARTICLE -> ONE SMALL REQUEST -> STRICT JSON -> VALIDATE -> CACHE -> CHECKPOINT -> DISCARD REQUEST CONTEXT`

Rules:
- one matched publication material per semantic request;
- article semantic batch size is exactly 1;
- each request is a fresh OpenAI-compatible chat-completion payload containing only the system instruction plus that article's bounded packet;
- no previous article messages are included;
- no conversational thread/session state is reused;
- source packet size is hard-bounded by configuration;
- model output size is hard-bounded by configuration;
- process requests sequentially by default;
- validate every response against `article_semantic_audit` schema;
- persist raw/parsed response to disk immediately;
- checkpoint `semantic_audit.json` after every article;
- cache successful calls so a provider failure or new controller chat resumes without repeating completed articles;
- only compact progress/summary is printed back to the interactive controller;
- full article responses remain on disk, not in interactive Hermes context.

This invariant exists because the local model may become unstable in very long interactive contexts even when its nominal context window is larger.

Deterministic extraction should resolve obvious UDC, DOI, ORCID, ABSTRACT, KEYWORDS, TABLE_CAPTION, FIGURE_CAPTION and REF_TITLE signals before Hermes is called. Hermes is primarily for unresolved AUTHOR / coauthor / supervisor / affiliation / degree-position / title / section semantics and ambiguity review.

## 12. Failure modes
Handle:
- timeout;
- HTTP 500;
- connection refused;
- model missing;
- invalid JSON;
- schema mismatch;
- truncated output;
- context overflow;
- empty response;
- low confidence;
- contradictory answers.

Behavior:
1. bounded retry only for transient failures;
2. schema-validate every response;
3. never write unvalidated output into authoritative manifest;
4. try configured fallback when main runtime fails;
5. use deterministic parsing where possible;
6. otherwise create review item;
7. unresolved required identity/content item => BLOCKED.

During the initial Astra development session, failure of both real Hermes endpoints => `BLOCKED_HERMES_BOOTSTRAP`.

## 13. Cache
Cache key includes:
- SHA-256 normalized input;
- task type;
- prompt/schema version;
- model id;
- relevant config hash.

Persist request, raw response, parsed response, model, endpoint, latency, retries and cache key.

## 14. Context-saving behavior
Write raw responses to:
`runs/<run_id>/hermes/responses/*.json`

Then reduce them into:
- `source_index.json`;
- `matches.json`;
- `metadata.json`;
- `ambiguities.md`.

Astra continues from these compact files.

## 15. Core invariant
Hermes is a real working subagent from the beginning of the Astra session, not decorative documentation.

Hermes may reduce Astra context use and semantic workload.
Hermes may never become a hidden source of truth or mutation authority.
