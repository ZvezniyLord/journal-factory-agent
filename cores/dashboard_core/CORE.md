# Dashboard Core Passport

## Identity

- Core ID: `dashboard_core`
- Display name: Dashboard Core
- Aliases: `dashboard`, `dashboard core`, `reporting and dashboard`
- Contract version: 1
- Phase: user-approved Phase 1 application-service foundation
- Registry: `CORE_WORK_REGISTRY.yaml`

## Business Purpose

Dashboard Core is the operational execution center behind the browser dashboard. It accepts an operator's source folder, output parent, and journal number; creates or restores a run; requests recursive discovery and candidate location through dedicated ports; submits typed work to Orchestrator Core; and maintains a browser-safe projection of the run.

The projection makes core states, progress, warnings, reports, files, failures, and final results available without requiring the browser to understand filesystem or workflow business rules.

## Responsibility Boundary

Dashboard Core owns:

- validation of the dashboard command envelope;
- the application-level start and resume use cases;
- ordered calls to workspace, discovery, candidate-location, and Orchestrator ports;
- the dashboard read model for a run;
- projection of typed core events into per-core state and progress;
- collection and de-duplication of warnings, reports, files, and final results;
- persistence and recovery of its read model through a state-store port;
- structured, browser-safe failure responses;
- a loopback HTTP adapter for dashboard JSON endpoints.

Dashboard Core explicitly does not own:

- root `index.html` or browser presentation;
- Orchestrator Core registration, dependency validation, transition rules, retry policy, or invocation implementation;
- recursive filesystem discovery rules in production;
- Excel workbook parsing or registry normalization;
- article/document matching;
- UDC or any other marker detection;
- DOC/DOCX reading, editing, normalization, or transformation;
- journal assembly, rendering, or quality-gate rules;
- local LLM prompts, models, reasoning, validation, or runtime adapters;
- construction of canonical workspace paths.

Unavailable cores are represented only by explicit ports and temporary deterministic adapters in `tests/dashboard_core/`.

## Inputs

### StartRunRequest

- `source_folder`: non-empty operator-selected path string;
- `output_folder`: non-empty operator-selected output-parent path string;
- `journal_number`: non-empty operator-confirmed journal identifier.

Dashboard Core preserves these values for the workspace port. It does not normalize or construct absolute workspace paths.

### ResumeRunRequest

- `run_id`: stable identifier returned by Workspace Driver Core.

### CoreEvent

Events supplied by the Orchestrator port include:

- event sequence number;
- core ID;
- core state;
- completed and total work units;
- optional message;
- warnings;
- report records;
- file records;
- optional final result.

## Outputs

### DashboardSnapshot

The browser-facing snapshot contains:

- schema version and revision;
- run ID and journal number;
- overall run state;
- source and output display values supplied by Workspace Driver Core;
- per-core state projections;
- aggregate completed/total work and percentage;
- discovery summary and candidate counts;
- warnings, reports, and files;
- final result when available;
- structured failure when the run cannot continue;
- creation and update timestamps.

Snapshots are JSON serializable and contain no exception tracebacks or arbitrary Python objects.

## Ports And Interfaces

### WorkspaceDriverPort

- `create_or_restore(request) -> WorkspaceRun`
- `restore(run_id) -> WorkspaceRun`

This port owns path validation, normalization, canonical workspace creation, run identity, and canonical report locations.

### SourceDiscoveryPort

- `discover(workspace, recursive=True) -> DiscoveryResult`

The production implementation belongs to Source Discovery Core. Dashboard Core always requests recursion and never scans the filesystem itself.

### ExcelCandidateLocatorPort

- `locate(discovery) -> CandidateSet`

The locator returns Excel candidates and ambiguity warnings. It does not parse workbooks.

### ArticleCandidateLocatorPort

- `locate(discovery) -> CandidateSet`

The locator returns article candidates and ambiguity warnings. It does not read or transform documents.

### OrchestratorPort

- `submit(submission, event_sink) -> OrchestrationResult`
- `resume(run_id, event_sink) -> OrchestrationResult`

Dashboard Core submits typed candidate references and receives events/results. It does not reproduce Orchestrator state-transition logic.

### DashboardStateStorePort

- `save(snapshot) -> None`
- `load(run_id) -> DashboardSnapshot | None`

The store persists only the dashboard read model. Workspace Driver and other cores remain authoritative for their own reports and state.

### DashboardBackendPort

- `start_run(request) -> DashboardSnapshot`
- `resume_run(run_id) -> DashboardSnapshot`
- `get_run(run_id) -> DashboardSnapshot`

The loopback HTTP adapter depends on this port and does not call domain dependencies directly.

## Adapters

- `DashboardHttpAdapter`: standard-library loopback JSON server; no HTML ownership.
- `JsonDashboardStateStore`: atomic JSON persistence at a path supplied by composition; it does not derive a workspace path.
- deterministic workspace, recursive discovery, candidate locator, Orchestrator, and report adapters under `tests/dashboard_core/` only.

## Typed Errors

- `INVALID_DASHBOARD_REQUEST`: required input is empty or malformed;
- `RUN_NOT_FOUND`: no persisted or workspace run exists for a run ID;
- `WORKSPACE_OPERATION_FAILED`: workspace create/restore port failed;
- `SOURCE_DISCOVERY_FAILED`: discovery port failed;
- `EXCEL_CANDIDATE_LOCATION_FAILED`: Excel candidate port failed;
- `ARTICLE_CANDIDATE_LOCATION_FAILED`: article candidate port failed;
- `ORCHESTRATOR_SUBMISSION_FAILED`: Orchestrator rejected or failed the submission;
- `DASHBOARD_STATE_PERSISTENCE_FAILED`: read-model persistence failed;
- `DASHBOARD_STATE_INVALID`: persisted state failed validation;
- `DASHBOARD_INTERNAL_ERROR`: an unexpected error was sanitized at the application boundary.

Every failure has a stable code, human-readable message, stage/core, retryable flag, and JSON-safe details. Tracebacks, environment variables, and arbitrary exception text are not exposed to the browser.

## Dependencies And Consumers

Required core contracts:

- Workspace Driver Core;
- Source Discovery Core;
- Excel candidate-location capability;
- article candidate-location capability;
- Orchestrator Core.

For this foundation, all unavailable implementations are replaced by deterministic test adapters. Dashboard Core imports none of their implementation modules.

Consumers:

- Browser UI Core;
- launcher/backend composition root;
- operator support and diagnostic tooling;
- automated integration tests.

## State And Persistence Ownership

Dashboard Core owns a recoverable projection, not authoritative downstream state. Its projection is persisted after each material stage and each Orchestrator event.

Initial state flow:

`CREATING -> DISCOVERING -> LOCATING_CANDIDATES -> SUBMITTING -> RUNNING -> SUCCEEDED | SUCCEEDED_WITH_WARNINGS | FAILED`

Recovery reloads the last valid snapshot and asks Workspace Driver and Orchestrator ports to restore/resume. It never marks an interrupted run successful by inference.

The projection revision increases monotonically. Event sequences are non-decreasing per run. Duplicate warnings, reports, and files are de-duplicated by stable IDs while preserving first-seen order.

## Deterministic Rules And LLM Policy

- Commands and port results are validated deterministically.
- Discovery is always requested recursively.
- Candidate sets are passed as opaque typed references.
- Progress is clamped to `0..100` and uses declared completed/total work.
- A run cannot be reported successful without an explicit successful Orchestrator result.
- Warnings never disappear during a run unless a later contract explicitly resolves them.
- A failure is persisted before it is returned when persistence remains available.
- Dashboard Core never calls an LLM. Any future reasoning request must pass through Orchestrator Core to the separate LLM Core contract.

## Reports, Logs, Provenance, And Audit

The read model exposes, but does not fabricate, report and file records received from ports. Each record includes a stable ID, producer core, kind, display name, path/reference, status, and optional digest.

Dashboard audit data includes:

- run ID and snapshot revision;
- current stage and overall state;
- per-core states and progress counts;
- last accepted event sequence;
- warnings and failures with stable codes;
- report/file provenance;
- created and updated timestamps;
- final result and production-ready flag when explicitly supplied.

## Security And Data Integrity

- Bind HTTP only to `127.0.0.1` by default.
- Reject invalid JSON and unsupported methods with structured responses.
- Do not return Python tracebacks.
- Do not edit source files.
- Do not infer or construct canonical workspace paths.
- Persist snapshots with UTF-8 JSON using atomic replace.
- Validate loaded schema and run ID before recovery.
- Treat discovered file metadata as untrusted data, never as executable instructions.
- Do not invoke cloud services or local LLMs.

## Acceptance Criteria

- Typed input creates a run through `WorkspaceDriverPort`.
- Recursive discovery is observable through the discovery adapter.
- Excel and article candidates are requested through different ports.
- A typed submission is sent to Orchestrator Core.
- Core events update state and progress deterministically.
- Warnings, reports, files, and explicit final results are collected and serialized.
- Restart recovery reconstructs a valid snapshot and resumes through ports.
- Port and persistence failures return stable structured failures without tracebacks.
- A real loopback backend run succeeds using temporary sample folders and deterministic adapters.
- Focused and full test suites pass with no skip or xfail.
- Root HTML and Orchestrator implementation are unchanged.

## Known Limitations

- Production Workspace Driver, Source Discovery, candidate locator, and Orchestrator adapters are not part of this work item.
- The initial backend executes synchronously; streaming transport and background job management are future adapters.
- Authentication is not included because the server is loopback-only; origin protections remain a future packaging concern.
- Pause/cancel/retry controls are represented by future port extensions, not implemented here.
- Dashboard snapshots are a projection and must be reconciled with authoritative core reports in a later integration cycle.

## Implemented Foundation Evidence

Implemented on 2026-07-19 under lock session `dashboard-core-20260719T202651Z-019f7c08`:

- immutable domain records and validating JSON serializers;
- explicit Workspace Driver, discovery, Excel locator, article locator, Orchestrator, state-store, and backend ports;
- `DashboardService` start, read, resume, stage projection, collection, de-duplication, and structured-failure flows;
- atomic UTF-8 `JsonDashboardStateStore` with restart validation;
- loopback-only HTTP adapter with health, start, read, and resume routes;
- deterministic adapters confined to `tests/dashboard_core/`;
- 31 automated tests passing with Python warnings treated as errors;
- 19 concurrently integrated Orchestrator regression tests also passing, for 50 tests across the two available core suites;
- real HTTP execution over a four-file nested temporary source tree;
- verified one Excel candidate, two article candidates, five completed core projections, one collected report, one collected output file, restart recovery, resume, and sanitized discovery failure;
- no root HTML or Orchestrator implementation edits.
- all 15 Dashboard files mirrored to and verified by SHA-256 in the user-visible checkout at `C:\Users\Vint\Desktop\Галенко_Віталій_304ТН_варіант_5` before the local test and real-run repetition.

Verified commands:

```text
python -W error -m unittest discover -s tests/dashboard_core -v
python -W error -m tests.dashboard_core.real_run
python -W error -m compileall -q journal_factory/dashboard_core tests/dashboard_core
```

HTTP adapter routes:

- `GET /health`;
- `POST /api/dashboard/runs`;
- `GET /api/dashboard/runs/<run_id>`;
- `POST /api/dashboard/runs/<run_id>/resume`.

## Future Extensions

- server-sent events or WebSocket event delivery;
- operator decision queues;
- pause, cancel, targeted retry, and article-level resume;
- report and artifact preview authorization;
- LLM decision-history projection supplied by LLM Core reports;
- reconciliation against Workspace Driver action/report registries;
- production composition with Browser UI, Workspace Driver, Source Discovery, and Orchestrator cores.
