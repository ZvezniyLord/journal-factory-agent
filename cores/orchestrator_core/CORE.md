# Orchestrator Core Passport

## Identity

- Core ID: `orchestrator_core`
- Display name: Orchestrator Core
- Aliases: `orchestrator`, `orchestrator core`, `оркестратор`, `ядро оркестратора`
- Phase: 1 foundation
- Passport owner: Orchestrator Core lock owner

## Business Purpose

The Orchestrator Core is the deterministic conductor of a Journal Factory run. It
registers callable cores, validates their dependencies, routes typed invocation
requests, applies legal run-state transitions, enforces bounded retry and failure
policies, coordinates pause/resume, and emits an auditable action history.

It decides *when* a core may run and *where* a result is routed. It never decides
the domain result that a core should produce.

## Responsibility Boundary

The core owns:

- runtime core registration and duplicate-registration rejection;
- dependency graph validation and deterministic pipeline ordering checks;
- run identity and in-memory execution state for the active conductor instance;
- legal transition enforcement;
- typed invocation request creation and typed result handling;
- bounded retries for results explicitly marked retryable;
- explicit `fail_run`, `pause_run`, and `continue_with_warning` failure routes;
- cooperative pause requests acknowledged between core invocations;
- resume from a paused in-memory run snapshot;
- append-only action events through an injected logging port;
- read-only state snapshots for UI adapters.

The core explicitly excludes:

- source discovery, Excel parsing, matching, UDC detection, DOCX processing,
  normalization, assembly, rendering, or quality decisions;
- filesystem path construction or workspace creation;
- Dashboard state aggregation, report presentation, or operator workflow design;
- HTTP and HTML business rules;
- direct persistence implementations;
- threads, process management, distributed scheduling, or background job queues;
- model loading, prompts, inference, embeddings, or LLM retry policy.

## Inputs

- `CoreDescriptor`: core ID, dependencies, retry limit, and failure route.
- `CoreInvocationPort`: callable adapter registered for one descriptor.
- `RunRequest`: run ID, ordered pipeline, per-core payloads, and dependencies that
  were satisfied before this conductor instance began.
- `PauseRequest`: run ID and operator/system reason.
- `ResumeRequest`: run ID.
- `CoreInvocationResult`: typed success, retryable failure, or terminal failure.

Payloads are opaque mappings. The Orchestrator may copy, log metadata about, and
route them, but it may not interpret domain fields.

## Outputs

- `RunSnapshot`: current state, current/next core, completed cores, attempts,
  warnings, failure, pause reason, and monotonically increasing revision.
- `CoreInvocationRequest`: request ID, run ID, core ID, operation, attempt, and
  opaque payload.
- `ActionRecord`: sequence, timestamp, run ID, core ID when applicable, action,
  status, attempt, message, and structured details.
- Stable typed exceptions for invalid commands before invocation.

## Ports, Adapters, and Interfaces

- `OrchestratorPort`: begin, advance, request pause, resume, and snapshot.
- `CoreInvocationPort`: accepts `CoreInvocationRequest` and returns
  `CoreInvocationResult`.
- `ActionLogPort`: append an `ActionRecord`; production persistence belongs to a
  Workspace/Reporting adapter.
- `ClockPort`: supplies UTC timestamps for reproducible tests.
- `LLMCorePort`: future explicit boundary accepting `LLMTaskRequest` and returning
  `LLMTaskResponse`. The Orchestrator does not implement this port.
- `InMemoryActionLog`: Phase 1 smoke/test adapter only.
- Local HTTP adapter: maps commands and snapshots to JSON without owning state
  transition rules.

All ports point inward. Domain modules import no HTTP, filesystem, DOCX, Excel,
database, Docker, Ollama, or browser packages.

## Typed Errors

- `CORE_ID_INVALID`
- `CORE_ALREADY_REGISTERED`
- `CORE_NOT_REGISTERED`
- `CORE_RETRY_LIMIT_INVALID`
- `CORE_DEPENDENCY_UNKNOWN`
- `CORE_DEPENDENCY_CYCLE`
- `PIPELINE_EMPTY`
- `PIPELINE_CORE_DUPLICATE`
- `PIPELINE_DEPENDENCY_UNSATISFIED`
- `RUN_ALREADY_ACTIVE`
- `RUN_NOT_FOUND`
- `RUN_ID_MISMATCH`
- `RUN_TRANSITION_INVALID`
- `RUN_NOT_PAUSED`
- `CORE_RESULT_INVALID`
- `CORE_INVOCATION_EXCEPTION` (typed invocation failure)
- `ACTION_LOG_WRITE_FAILED`

Domain failures returned by invoked cores remain structured `InvocationError`
values and are never converted to unhandled tracebacks for an adapter.

## Dependencies and Consumers

Production dependencies:

- Workspace Driver Core for canonical run/report locations and persisted action
  history through ports;
- registered domain cores through `CoreInvocationPort` implementations;
- a future state-store adapter for restart-safe resume.

Phase 1 does not require those implementations. Tests and smoke launch use
in-memory adapters and a deterministic demonstration core.

Consumers:

- Dashboard Core via `OrchestratorPort` and read-only `RunSnapshot`;
- local HTTP adapter;
- future launch/recovery service;
- reporting and QA consumers of action events.

## State and Persistence Ownership

Run states are:

`idle -> validating -> running -> pause_requested -> paused -> running`

Terminal routes are:

`running -> completed | completed_with_warnings | failed`

Validation may route to `failed`. Terminal states do not transition in the same
instance. Starting another run requires a new Orchestrator instance, which keeps
run histories isolated.

The core owns only the active in-memory state and snapshot schema. Durable state,
paths, JSONL files, and recovery storage belong to adapters supplied through
ports. Action records are append-only and sequence ordered.

## Deterministic Rules

1. Core IDs use lowercase ASCII letters, digits, and underscores.
2. Registration is unique and rejects self-dependencies.
3. Every dependency must be registered before a run can begin.
4. The requested pipeline order must place each dependency before its consumer,
   unless it appears in `pre_satisfied_dependencies`.
5. One `advance` command invokes at most one pipeline core, including its bounded
   retry attempts.
6. Retry count is `max_retries`; one uninterrupted advance cycle performs at
   most `1 + max_retries` attempts. A manual resume after a `pause_run` route
   starts a new bounded cycle and keeps attempt IDs monotonic.
7. Only a typed retryable failure may be retried.
8. Pause is cooperative and is acknowledged before the next invocation.
9. Resume is legal only from `paused` for the same run ID.
10. Failure routing comes only from the registered descriptor.
11. Every material command, transition, attempt, retry, warning, and terminal
    result emits an action record.
12. Opaque payload content cannot change routing policy.

## LLM Boundary

LLM access is not implemented in this core. A future LLM Core is invoked only
through `LLMCorePort` using a structured request containing task ID, purpose,
evidence references, constraints, response schema, and confidence requirement.
Its response contains structured output, confidence, provenance, validation
status, warnings, and error data.

No Orchestrator code may load model weights, create prompts, call Ollama or a cloud
API, validate domain semantics, or allow an LLM response to mutate a document.

## Reports, Logs, Provenance, and Audit

Every `ActionRecord` contains:

- schema version;
- monotonic sequence;
- UTC timestamp;
- run ID;
- core ID when applicable;
- action and status;
- invocation attempt when applicable;
- human-readable message;
- structured details without tracebacks or secrets.

Request IDs are deterministic within a run: `<run_id>:<core_id>:<attempt>`.
Snapshots expose action count and revision so adapters can detect stale views.

## Security and Data Integrity

- Treat invocation payloads and core results as untrusted structured data.
- Never execute strings from payloads as code or shell commands.
- Never expose Python tracebacks through HTTP responses.
- Never mutate caller-provided payload mappings.
- Never write source documents or construct absolute workspace paths.
- Bound retries to prevent infinite loops.
- Log stable error codes, not credentials or private document text.
- Bind the smoke HTTP adapter only to `127.0.0.1`.

## Acceptance Criteria

- Registration, dependency validation, legal transitions, routing, retries,
  pause/resume, failure routes, and logging are covered by deterministic tests.
- Positive, negative, boundary, recovery, and HTTP integration tests pass.
- Invalid commands return stable typed errors.
- Retry exhaustion terminates or routes exactly as declared.
- The root HTML is a thin adapter that can start a demonstration run and display
  the live Orchestrator state.
- Dashboard Core implementation paths are unchanged.
- LLM contracts exist only as an explicit future port and structured types; no
  LLM runtime or call is present.
- A real loopback smoke launch serves HTML, calls the API, completes a run, and
  shuts down cleanly.
- Focused tests, full tests, artifact inspection, architecture review, and
  repository acceptance are recorded in the development plan.

## Known Limitations

- Phase 1 execution is single-process and cooperative.
- Resume is in-memory; process-restart recovery needs a future state-store adapter.
- The command menu runs a deterministic demonstration core, not document work.
- No concurrency or parallel branches are scheduled.
- No production Workspace Driver adapter exists in this core.

## Future Extensions

- durable snapshot/replay adapter through Workspace Driver ports;
- cancellation and operator approval states;
- DAG scheduling with explicitly bounded parallelism;
- timeouts and circuit breakers owned by invocation adapters;
- versioned pipeline definitions and migration;
- Dashboard integration through the existing read-only snapshot contract;
- LLM Core registration as a normal typed dependency without special-case logic.
