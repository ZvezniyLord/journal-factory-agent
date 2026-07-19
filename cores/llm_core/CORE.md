# LLM Core Passport

## Identity

- Core ID: `llm_core`
- Display name: LLM Core
- Aliases: `llm`, `llm core`, `local llm`, `lm studio`, `ollama`, `локальна модель`, `ядро llm`, `ядро локальної моделі`
- Registry: `CORE_WORK_REGISTRY.yaml`
- Current phase: `future`
- Current status: `planned`
- Active lock: none

## Business purpose

LLM Core is the only component allowed to communicate with model runtimes. It provides a provider-neutral, typed, auditable reasoning boundary for every other Journal Factory core.

Other cores submit structured tasks, evidence, constraints, required response schema, confidence requirements, and correlation metadata. They must never invoke LM Studio, Ollama, OpenAI-compatible endpoints, model weights, or provider SDKs directly.

## Responsibility boundary

LLM Core owns:

- deterministic endpoint discovery from an explicit allowlist;
- provider health checks and model enumeration;
- provider and model selection;
- request normalization;
- native Ollama and OpenAI-compatible adapters;
- LM Studio integration;
- structured JSON generation and validation;
- bounded retry, cooldown, circuit-breaker, and fallback behavior;
- normalized errors;
- masked configuration;
- latency, usage, correlation IDs, provenance, and diagnostic reports;
- host, Docker-host, Docker-service, and Compose-network connectivity rules.

LLM Core does not own:

- document parsing or transformation;
- retrieval, matching, UDC detection, segmentation, rendering, or QA domain logic;
- orchestration state transitions;
- dashboard presentation;
- downloading large models without explicit approval;
- opening model services to external networks;
- broad LAN or port scanning;
- hidden prompt execution outside structured requests.

## Dependencies

- Workspace Driver Core for canonical report and log paths.
- Orchestrator Core for typed invocation, lifecycle, retry ownership boundaries, and action records.

## Consumers

Any core that requires ambiguous reasoning, classification, comparison, structured extraction, or confidence-aware escalation must call the LLM Core port.

## Required ports and contracts

The exact implementation language may follow repository conventions, but the domain boundary must provide equivalents of:

```python
class LLMCorePort:
    async def health_check(self, request: HealthCheckRequest) -> HealthResult: ...
    async def list_models(self, request: ListModelsRequest) -> list[ModelInfo]: ...
    async def chat(self, request: ChatRequest) -> ChatResponse: ...
    async def generate_json(self, request: StructuredRequest) -> StructuredResponse: ...
```

A normalized response must include:

- provider;
- endpoint;
- model;
- text;
- structured data when requested;
- latency;
- usage when available;
- finish reason;
- request or correlation ID;
- timestamp;
- attempt count;
- fallback chain;
- normalized error;
- raw non-secret metadata.

## Provider adapters

Required adapter families:

1. LM Studio through OpenAI-compatible API.
2. Ollama native API.
3. Ollama OpenAI-compatible API.
4. Explicitly configured custom OpenAI-compatible endpoint.

Provider-specific HTTP formats must remain inside adapters. Domain consumers receive only normalized contracts.

## Deterministic endpoint discovery

Candidate sources, in priority order:

1. explicit CLI configuration;
2. environment variables;
3. repository configuration;
4. Docker service names;
5. `host.docker.internal`;
6. Docker default gateway;
7. localhost addresses;
8. other addresses explicitly present in approved configuration.

Typical allowed candidates include:

- `http://127.0.0.1:1234/v1`
- `http://localhost:1234/v1`
- `http://host.docker.internal:1234/v1`
- `http://127.0.0.1:11434`
- `http://localhost:11434`
- `http://host.docker.internal:11434`

Rules:

- never scan arbitrary LAN ranges;
- never scan all ports;
- never use `0.0.0.0` as a client destination;
- never append `/v1` twice;
- prefer Docker service names over magic IP addresses;
- use `host-gateway` support on Linux where required.

## API checks

OpenAI-compatible adapters:

- `GET /v1/models`
- `POST /v1/chat/completions`

Ollama native adapter:

- `GET /api/tags`
- `GET /api/version` when supported
- `POST /api/chat`

Diagnostics must distinguish DNS, TCP, HTTP, API, model-list, inference, and structured-JSON failures.

## Model selection

When a model is explicit, verify that it exists. When `model=auto`, select deterministically from the returned model list and record the reason. Never invent a model name. Embedding-only models must not be selected for chat.

## Retry and fallback

Fallback may occur for transient connectivity, timeout, DNS, HTTP 5xx, temporary model unavailability, or malformed server responses. It must not hide authentication failures, invalid configuration, an absent explicitly requested model, or invalid caller schema.

Retries must be bounded. Infinite loops are forbidden.

## Security and integrity

- Never commit real API keys.
- Mask authorization headers and secret environment values.
- Keep real `.env` files out of Git.
- Do not log private prompt bodies by default in production.
- Do not download large models automatically without explicit approval.
- Do not bind model services externally unless explicitly approved.

## Reports and provenance

Machine-readable diagnostics must include environment type, checked candidates, discovery source, DNS/TCP/HTTP/API results, models, selected model, latency, inference result, fallback chain, normalized errors, masked effective configuration, and component versions.

Canonical runtime report locations must be obtained through Workspace Driver Core, with expected logical names equivalent to:

- `reports/llm-scan.json`
- `reports/llm-scan.md`
- append-only LLM call provenance records.

## Typed errors

At minimum distinguish:

- configuration error;
- endpoint unavailable;
- DNS failure;
- connection failure;
- timeout;
- authentication or authorization failure;
- unsupported API;
- no models available;
- requested model unavailable;
- invalid provider response;
- invalid structured response;
- retry exhausted;
- all providers unavailable.

## Acceptance criteria

The core is accepted only when:

1. all provider adapters satisfy the same typed port;
2. deterministic discovery and URL normalization are covered by tests;
3. unit tests use HTTP mocks;
4. integration smoke tests are separate;
5. Docker Compose configuration validates;
6. a diagnostic CLI runs with stable exit codes;
7. a real scan is performed against allowed endpoints;
8. a real short inference is performed when a model is available;
9. absence of a model produces a controlled report rather than a crash;
10. retries and fallback are bounded and auditable;
11. secrets are masked;
12. repository acceptance passes.

## Phase gate

Registration and documentation are present, but implementation is not approved while the repository remains in Phase 1 with local LLM integration explicitly excluded.

A future agent must not claim or implement this core until the user explicitly approves the LLM Core phase and the registry is updated accordingly.
