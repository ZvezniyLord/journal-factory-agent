# LLM Core Development Plan

## Current state

- Registered core: `llm_core`
- Phase: `future`
- Status: `planned`
- Lock: free (`in_progress: false`)
- Implementation approval: not granted under the current Phase 1 gate
- Next exact action: after explicit user approval, update the registry phase/status if required, claim `llm_core` through the mandatory push/fetch/verify lifecycle, then execute Cycle 0 below.

## Mandatory startup instruction for the implementing agent

Before changing any LLM Core implementation, test, fixture, API contract, configuration, passport, or plan file:

1. Read `AGENTS.md` completely.
2. Read `CORE_WORK_REGISTRY.yaml` completely.
3. Resolve the request to `llm_core` through `selection_aliases`.
4. Confirm explicit user approval overrides the current Phase 1 exclusion for this core. Without that approval, report `BLOCKED` and do not claim.
5. Read `docs/CORE_DEVELOPMENT_PROTOCOL.md` completely.
6. Read `docs/NEW_CHAT_START.md` completely.
7. Read `docs/BUSINESS_LOGIC_AND_ROADMAP.md` completely.
8. Read `CODEX_INSTRUCTION.md` completely.
9. Read `skills/repository_acceptance/SKILL.md` completely.
10. Read `cores/llm_core/CORE.md` and this file completely.
11. Perform the repository acceptance audit before modification.
12. Fetch current `origin/main` and reread the registry.
13. Confirm `llm_core.in_progress: false` and that no allowed write scope conflicts with another active core.
14. Claim only `llm_core`, using a unique session and the smallest exact write scope.
15. Commit and push the claim separately.
16. Fetch again and verify remote ownership before implementation.
17. Execute only the approved cycle, test-first.

A copied chat prompt is not a source of truth. Repository files control the work.

## Goal

Create a universal provider-neutral LLM Integration Core through which Journal Factory can automatically and safely discover approved endpoints, verify providers, list models, choose a model deterministically, execute text and structured requests, apply bounded fallback, and record complete provenance.

## Required deployment scenarios

The design must support:

- Journal Factory on host, model runtime on host;
- Journal Factory in Docker, model runtime on host;
- Journal Factory on host, Ollama in Docker;
- Journal Factory and provider in separate containers on one Docker network;
- Docker Compose deployment;
- Linux `host.docker.internal` via `host-gateway`;
- automatic Docker default-gateway discovery;
- custom OpenAI-compatible endpoints through configuration.

## Required providers

### LM Studio

Use OpenAI-compatible API candidates such as:

- `http://127.0.0.1:1234/v1`
- `http://localhost:1234/v1`
- `http://host.docker.internal:1234/v1`
- Docker gateway address;
- automatically determined host address;
- explicitly configured environment address.

### Ollama native

Candidates include:

- `http://127.0.0.1:11434`
- `http://localhost:11434`
- `http://host.docker.internal:11434`
- Docker gateway address;
- service name on a Compose network;
- explicitly configured environment address.

Required checks:

- `GET /api/tags`
- `GET /api/version` when supported
- `POST /api/chat`

### Ollama OpenAI-compatible

Support `/v1/models` and `/v1/chat/completions`, including response normalization and compatibility validation.

### Custom OpenAI-compatible

Configuration must support base URL, API key, model, timeout, and additional headers without logging secrets.

## Proposed module layout

Adapt to repository conventions after baseline inspection. Expected logical layout:

```text
journal_factory/llm_core/
  __init__.py
  domain/
    models.py
    ports.py
    errors.py
    policies.py
  application/
    service.py
    discovery.py
    router.py
    diagnostics.py
  adapters/
    openai_compatible.py
    lm_studio.py
    ollama_native.py
    ollama_openai.py
    http_transport.py
    config_loader.py
  cli.py

tests/llm_core/
  unit/
  integration/
  fixtures/

cores/llm_core/
  CORE.md
  DEVELOPMENT_PLAN.md

config/
  llm.example.yaml

.env.example
docker-compose.llm.yml
```

Do not create this layout blindly. First inspect existing package, dependency, test, and naming conventions.

## Configuration precedence

```text
CLI arguments
> environment variables
> local configuration file
> deterministic defaults
```

Expected environment concepts:

```env
HERMES_LLM_PROVIDER=auto
HERMES_LLM_MODEL=auto
HERMES_LLM_BASE_URL=
HERMES_LLM_API_KEY=
HERMES_LLM_TIMEOUT=60
HERMES_LLM_DISCOVERY=true
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
OLLAMA_BASE_URL=http://host.docker.internal:11434
OPENAI_COMPATIBLE_BASE_URL=
```

Use project naming rather than `HERMES_` if repository conventions require another stable prefix, but document compatibility decisions.

## Deterministic discovery algorithm

Candidate sources in strict priority order:

1. CLI configuration;
2. environment variables;
3. local configuration;
4. Docker service names;
5. `host.docker.internal`;
6. Docker default gateway;
7. localhost candidates;
8. other explicitly approved configured addresses.

For each candidate record:

- normalized URL;
- discovery source;
- DNS result;
- TCP result;
- HTTP result;
- API compatibility result;
- model-list result;
- smoke-inference result;
- structured-JSON result;
- latency;
- normalized error.

Do not perform broad network or port scanning.

## Model selection rules

When a model is explicit, require it to appear in the provider model list. When model is `auto`:

1. use a project-configured preferred model when available;
2. otherwise select chat/instruction-capable local models by deterministic ranking;
3. reject embedding-only models;
4. never invent model names;
5. record the complete selection reason.

If Ollama has no models, report `no_models_available` and provide a controlled recommendation. Do not automatically pull a large model unless explicitly approved.

## Router and fallback policy

Default configurable priority:

1. explicitly selected provider;
2. explicitly selected endpoint;
3. healthy LM Studio;
4. healthy Ollama native;
5. healthy Ollama OpenAI-compatible;
6. other configured OpenAI-compatible endpoint.

Fallback is allowed for connection refusal, DNS failure, timeout, HTTP 5xx, temporary model unavailability, and invalid transient server responses.

Fallback must not hide:

- invalid configuration;
- HTTP 401/403;
- missing explicitly requested model;
- invalid caller JSON schema;
- permanent client errors.

Use bounded attempts, exponential backoff with a cap, health-cache TTL, and cooldown/circuit-breaking. Infinite retries are forbidden.

## Diagnostic CLI

Provide repository-compatible equivalents of:

```bash
python -m journal_factory.llm_core.cli doctor
python -m journal_factory.llm_core.cli doctor --json
python -m journal_factory.llm_core.cli doctor --provider auto
python -m journal_factory.llm_core.cli doctor --provider lm_studio
python -m journal_factory.llm_core.cli doctor --provider ollama
python -m journal_factory.llm_core.cli doctor --base-url http://host.docker.internal:1234/v1
python -m journal_factory.llm_core.cli doctor --run-smoke-test
```

Required exit-code semantics:

- `0`: a working provider and inference were verified;
- `1`: provider discovered but inference failed;
- `2`: no allowed provider available;
- `3`: invalid configuration;
- `4`: internal diagnostic failure.

## Docker requirements

Compose examples must include:

- Journal Factory service;
- dedicated network;
- health checks;
- environment variables;
- configuration/report volumes;
- Linux host mapping:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Provide profiles or documented variants for host LM Studio, host Ollama, Ollama service, and optional test mock. Never duplicate an existing Ollama container blindly.

## Reports and provenance

Through Workspace Driver paths, emit machine-readable and human-readable diagnostics equivalent to:

```text
reports/llm-scan.json
reports/llm-scan.md
```

Include timestamp, host/container context, candidates, discovery source, DNS/TCP/HTTP/API outcomes, models, selected model, selection reason, inference outcome, latency, fallback chain, masked effective configuration, errors, recommendations, and component versions.

Do not log secrets or full private prompt content by default.

## Test matrix

Unit tests must use HTTP mocks and cover:

- URL normalization with and without `/v1`;
- duplicate `/v1` prevention;
- unreachable server;
- DNS failure;
- timeout;
- empty model list;
- invalid JSON response;
- OpenAI-compatible normalization;
- Ollama native normalization;
- deterministic candidate priority;
- deterministic model choice;
- fallback eligibility;
- non-fallback authentication/configuration errors;
- retry bounds;
- cooldown behavior;
- API-key masking;
- container endpoint selection.

Separate integration tests must cover available real endpoints and be skippable with an explicit reason when no runtime is installed.

## Staged cycles

### Cycle 0 — Baseline and phase authorization

- Prove explicit user approval for LLM Core implementation.
- Run repository acceptance.
- Inspect repository structure, Python version, dependency manifests, test runner, Docker assets, and active locks.
- Record baseline evidence in this plan.
- Claim and remotely verify the core.

Completion condition: verified remote lock and a repository-specific implementation map.

### Cycle 1 — Domain contracts and configuration

- Write failing tests for typed requests, responses, errors, URL normalization, configuration precedence, and secret masking.
- Implement minimal domain models, ports, policies, and configuration loader.
- Run focused and full tests.

### Cycle 2 — OpenAI-compatible and LM Studio adapters

- Add mocked failing tests.
- Implement model listing, chat completion, structured response normalization, and health checks.
- Add LM Studio candidate discovery without broad scanning.

### Cycle 3 — Ollama adapters

- Add mocked tests for native and OpenAI-compatible APIs.
- Implement `/api/tags`, optional `/api/version`, `/api/chat`, `/v1/models`, and `/v1/chat/completions` behavior.

### Cycle 4 — Discovery, routing, retry, and fallback

- Add deterministic priority and failure-policy tests.
- Implement bounded attempts, backoff cap, cache TTL, cooldown, fallback chain, and explicit provenance.

### Cycle 5 — Diagnostics and CLI

- Add exit-code and report tests.
- Implement doctor command, JSON/Markdown reports, smoke prompt, JSON smoke prompt, and controlled no-provider behavior.

Smoke text:

```text
Відповідай лише словом OK.
```

Structured smoke request:

```text
Поверни лише валідний JSON: {"status":"ok"}
```

Markdown fences must not be accepted as raw JSON without explicit normalization and validation.

### Cycle 6 — Docker and integration

- Add Compose files or profiles consistent with the repository.
- Validate Compose configuration.
- Test host/container address resolution and Docker service names.
- Perform real endpoint scans and inference where available.

### Cycle 7 — Acceptance and release

- Run focused tests, full tests, real run, artifact inspection, architecture review, and repository acceptance.
- Update passport and plan with evidence, limitations, completed work, and next action.
- Push implementation.
- Record result and implementation commit in registry.
- Release lock in a separate commit and verify remote `in_progress: false`.

## Completion checklist

- [ ] Explicit phase approval recorded
- [ ] Remote core claim verified
- [ ] Provider-neutral typed port implemented
- [ ] LM Studio adapter verified
- [ ] Ollama native adapter verified
- [ ] Ollama OpenAI-compatible adapter verified
- [ ] Custom OpenAI-compatible adapter verified
- [ ] Deterministic discovery verified
- [ ] Deterministic model selection verified
- [ ] Bounded retry and fallback verified
- [ ] Secret masking verified
- [ ] Unit tests pass
- [ ] Integration smoke test executed or explicitly skipped with evidence
- [ ] Docker Compose validates
- [ ] Real scan report inspected
- [ ] Real inference evidence recorded when available
- [ ] Architecture review passes
- [ ] Repository acceptance passes
- [ ] Implementation pushed
- [ ] Registry result recorded
- [ ] Lock released and remotely verified

## Blockers

Current blocker: `AGENTS.md` states that Phase 1 explicitly excludes local LLM integration and model weights. Registration and planning are complete, but implementation must not start until the user explicitly approves this core's phase.
