# Dashboard Core Development Plan

## Work Item

Build the port-driven Dashboard Core application-service foundation described in the user request and `CORE_WORK_REGISTRY.yaml`. The work must not edit root HTML or Orchestrator Core implementation and must use deterministic test adapters for unavailable cores.

## Inspected Baseline And Evidence

- Canonical repository: `https://github.com/ZvezniyLord/journal-factory-agent.git`.
- Baseline before registration: `19488c87e1f20ad1ae5ecef6eb3005956fbdba63`.
- Orchestrator registration: `0edc8fe`; Orchestrator claim observed at `b85be5d`.
- Dashboard registration: `e21fa6aab8056a11b0167ef1d5934453a58fcaee`.
- Dashboard claim: `a450062333937c41bbb09df05a062420699658f8`.
- Full navigation read: `AGENTS.md`, `CORE_WORK_REGISTRY.yaml`, `docs/CORE_DEVELOPMENT_PROTOCOL.md`, `docs/NEW_CHAT_START.md`, `docs/BUSINESS_LOGIC_AND_ROADMAP.md`, `CODEX_INSTRUCTION.md`, and `skills/repository_acceptance/SKILL.md`.
- The repository was a documentation-only bootstrap at claim time; no Dashboard implementation or tests existed.
- Orchestrator Core owns `cores/orchestrator_core/**`, `journal_factory/orchestrator_core/**`, `tests/orchestrator_core/**`, and root `index.html` under another active lock.
- Dashboard scope is disjoint: `cores/dashboard_core/**`, `journal_factory/dashboard_core/**`, and `tests/dashboard_core/**`.
- The current product phase forbids Excel parsing, document processing, UDC detection, matching, LLM reasoning, assembly, rendering, and production QA. This plan defines only ports and deterministic adapters for those boundaries.

## Assumptions And Open Questions

Assumptions for this cycle:

- The user's detailed request explicitly approves a Phase 1 Dashboard application-service foundation.
- Workspace Driver and Orchestrator implementations may arrive concurrently, so Dashboard imports only its own protocols and models.
- `source_folder` and `output_folder` remain opaque strings at the Dashboard boundary; Workspace Driver validates and normalizes them.
- A candidate locator is distinct from Excel parsing. It returns references only.
- Browser delivery can use request/response JSON for this cycle; live push transport can be added without changing the application port.
- Standard-library Python is preferred so the new core does not require a shared dependency-manifest edit.

Open integration questions, deliberately non-blocking for the port foundation:

- Exact shared model package for Workspace and Orchestrator contracts after their implementations land.
- Whether live updates will use polling, server-sent events, or WebSockets.
- Which Workspace Driver report key will be assigned to the dashboard projection.
- Whether operator pause/cancel belongs in the first browser integration cycle.

## Architecture And Domain Model

The implementation follows ports and adapters:

```text
HTTP adapter
    -> DashboardBackendPort
        -> DashboardService
            -> WorkspaceDriverPort
            -> SourceDiscoveryPort(recursive=True)
            -> ExcelCandidateLocatorPort
            -> ArticleCandidateLocatorPort
            -> OrchestratorPort(event sink)
            -> DashboardStateStorePort
```

Domain models:

- `StartRunRequest`, `WorkspaceRun`;
- `DiscoveredFile`, `DiscoveryResult`, `CandidateSet`;
- `WorkflowSubmission`, `OrchestrationResult`, `CoreEvent`;
- `CoreProjection`, `WarningRecord`, `ReportRecord`, `FileRecord`, `FinalResult`;
- `DashboardFailure`, `DashboardSnapshot`;
- `RunState` and `CoreState` enums.

Application rules:

- validate command envelopes before calling ports;
- persist after each material stage and accepted event;
- use a monotonic snapshot revision;
- convert known port failures into stage-specific dashboard failure codes;
- sanitize unknown exceptions as `DASHBOARD_INTERNAL_ERROR`;
- never report success without an explicit Orchestrator result;
- reconstruct snapshots from JSON through validating constructors.

## File And Module Layout

```text
cores/dashboard_core/
  CORE.md
  DEVELOPMENT_PLAN.md
journal_factory/dashboard_core/
  __init__.py
  models.py
  ports.py
  service.py
  persistence.py
  backend.py
tests/dashboard_core/
  __init__.py
  adapters.py
  test_models.py
  test_service.py
  test_persistence.py
  test_backend.py
  real_run.py
```

No root HTML, shared dependency manifest, or Orchestrator file is in scope.

## Staged Implementation Cycles

### Cycle 0 - Passport And Plan

1. Register and remotely verify `dashboard_core`.
2. Claim only Dashboard paths and remotely verify ownership.
3. Create this passport and detailed plan before implementation.
4. Review boundaries against the active Orchestrator lock.

Exit: documents are specific, complete, and no implementation file exists yet.

### Cycle 1 - Models And Serialization

Failing tests first:

- valid snapshot round-trips to/from JSON-safe dictionaries;
- invalid run state, negative progress, and mismatched totals are rejected;
- final production-ready state is never inferred;
- duplicate report/file/warning identities are stable.

Minimal implementation:

- immutable dataclasses and enums;
- validated `to_dict`/`from_dict` methods;
- typed failure model;
- deterministic UTC timestamp formatting supplied by the service clock.

Exit: focused model tests pass.

### Cycle 2 - Start Workflow And Event Projection

Failing tests first:

- source/output/journal request reaches Workspace Driver unchanged;
- discovery is requested with `recursive=True`;
- Excel and article locator ports are both called once with the same discovery result;
- Orchestrator receives a typed submission containing candidate references;
- events update per-core states, aggregate progress, warnings, reports, files, and final result;
- each material update is persisted.

Negative and boundary tests:

- blank request fields fail before ports are called;
- each port failure maps to its stable stage code;
- unexpected exceptions are sanitized;
- zero-total progress is handled without division by zero;
- duplicate records are de-duplicated in first-seen order.

Exit: service tests prove orchestration only through ports.

### Cycle 3 - Persistence And Restart Recovery

Failing tests first:

- JSON store saves atomically and reloads an identical snapshot;
- a second DashboardService instance reconstructs the first instance's run state;
- resume calls Workspace Driver restore and Orchestrator resume;
- missing state returns `RUN_NOT_FOUND`;
- invalid JSON/schema/run ID returns `DASHBOARD_STATE_INVALID`;
- write failure returns `DASHBOARD_STATE_PERSISTENCE_FAILED` without partial JSON.

Exit: restart recovery is deterministic and validated.

### Cycle 4 - Loopback Backend Adapter

Failing tests first:

- `GET /health` returns a stable JSON response;
- `POST /api/dashboard/runs` starts a run and returns its snapshot;
- `GET /api/dashboard/runs/{run_id}` returns recovered state;
- `POST /api/dashboard/runs/{run_id}/resume` resumes a run;
- invalid JSON, unknown routes, and unsupported methods return structured errors;
- unexpected failures never expose a traceback.

Minimal implementation:

- `ThreadingHTTPServer` adapter bound to `127.0.0.1` by default;
- thin handler calling only `DashboardBackendPort`;
- JSON request/response mapping.

Exit: backend adapter tests pass without root HTML.

### Cycle 5 - Real Backend Execution And Acceptance

1. Create a temporary nested source tree with a registry file, two article files, and an unrelated asset.
2. Compose the real loopback backend with temporary deterministic adapters.
3. Start a run over HTTP.
4. Verify recursive discovery saw all nested files.
5. Verify one Excel candidate and two article candidates.
6. Verify core-state events, aggregate progress, warning, report, file, and final result.
7. Stop the backend, construct a fresh service/store, and verify recovery over HTTP.
8. Inject a deterministic discovery failure and verify the structured error body.
9. Parse every persisted JSON artifact and inspect it against the contract.
10. Run focused tests, full tests, architecture review, and repository acceptance.

Exit: evidence is recorded below, implementation is pushed, and the lock is released.

## Test Case Matrix

Positive:

- new run succeeds with nested discovery;
- explicit report/file/final records reach the snapshot;
- completed-with-warning remains distinguishable from clean success;
- recovered run preserves revision and event sequence;
- loopback API returns deterministic JSON.

Negative:

- missing source/output/journal input;
- workspace create failure;
- source discovery failure;
- Excel locator failure;
- article locator failure;
- Orchestrator submission failure;
- state persistence failure;
- corrupt persisted JSON;
- invalid HTTP JSON and unknown route.

Boundary:

- no candidates;
- one candidate of each type;
- deeply nested candidates;
- zero total work;
- completed work greater than total from an invalid event;
- duplicate event sequence and duplicate report/file/warning IDs;
- Unicode file display names serialized as UTF-8;
- long but bounded human messages.

Recovery:

- restore after discovery;
- restore after Orchestrator event;
- restore terminal success without rerunning;
- resume interrupted run through Orchestrator port;
- requested run ID differs from persisted payload;
- persistence target disappears or becomes unwritable.

Integration:

- HTTP -> service -> all deterministic ports -> JSON store -> HTTP readback;
- service restart with the same state-store directory;
- structured failure round-trip through HTTP.

## Fixtures And Real-Run Samples

Tests create temporary data only:

```text
source/
  conference/
    registry.xlsx
    articles/
      alpha.docx
      nested/
        beta.doc
    assets/
      cover.png
output/
  dashboard-state/
```

The recursive discovery adapter uses `Path.rglob` only in test code. Candidate adapters classify file suffixes deterministically and do not open Excel or DOC/DOCX content.

The Orchestrator adapter emits a fixed sequence covering queued, running, warning, report, file, and success events. A failure variant raises a typed port error at a configured stage.

## Migration And Compatibility Risks

- Workspace and Orchestrator models may later differ. Keep conversion in adapters so Dashboard domain models remain stable.
- Shared API routes may be assigned by Browser UI Core. The backend routes in this cycle should be treated as version-1 adapter contracts and changed only through coordinated ownership.
- A synchronous start endpoint can block for production workloads. The application port remains compatible with a future background adapter.
- Persisted snapshots require schema versioning. Reject unknown future versions rather than silently misreading them.
- Windows atomic replace can fail while antivirus or another process holds a file; surface a retryable structured persistence failure.
- Local absolute paths are sensitive operational data; the browser adapter should expose only paths explicitly supplied/approved by Workspace Driver.

## Observability And Report Fields

Snapshot-level fields:

- `schema_version`, `revision`, `run_id`, `journal_number`;
- `state`, `stage`, `created_at`, `updated_at`;
- `source_folder`, `output_folder` from the workspace result;
- `last_event_sequence`;
- `completed_work`, `total_work`, `progress_percent`;
- `discovered_file_count`, `excel_candidate_count`, `article_candidate_count`;
- `cores`, `warnings`, `reports`, `files`, `final_result`, `failure`.

Record provenance:

- stable ID;
- producer core;
- kind/status;
- display name/message;
- path/reference supplied by the producing port;
- optional digest;
- event sequence where first observed.

## Manual Test Procedure

1. From repository root run `python -m unittest discover -s tests/dashboard_core -v`.
2. Run `python tests/dashboard_core/real_run.py --serve`.
3. Note the printed loopback URL and temporary source/output paths.
4. Open `<url>/health`; expect `{"status":"ok"}`.
5. Open the printed run URL; verify the snapshot shows discovered files, one Excel candidate, two article candidates, core progress, a warning, a report, a file, and an explicit successful final result.
6. Stop the process with Ctrl+C.
7. Run the printed recovery command; verify the same run ID and persisted state load after restart.
8. Run the printed failure command; verify a stable failure code and no traceback.

The exact commands may be adjusted after the real-run harness is implemented and must be updated here before release.

## Completion Checklist

- [x] Full repository navigation read.
- [x] Clean canonical clone and repository identity verified.
- [x] Dashboard Core registered separately.
- [x] Dashboard Core lock remotely verified.
- [x] Orchestrator and root HTML scopes confirmed disjoint.
- [x] Passport created before implementation.
- [x] Detailed plan created before implementation.
- [ ] Failing model tests added before model implementation.
- [ ] Failing service tests added before service implementation.
- [ ] Failing persistence tests added before persistence implementation.
- [ ] Failing backend tests added before backend implementation.
- [ ] Focused tests pass with no skip/xfail.
- [ ] Full suite passes with no skip/xfail.
- [ ] Real loopback backend run demonstrated with temporary folders.
- [ ] Recursive discovery, updates, collections, recovery, and failures inspected.
- [ ] Architecture review passes.
- [ ] Repository acceptance completed.
- [ ] Passport and plan updated with final evidence.
- [ ] Implementation pushed.
- [ ] Dashboard lock released and remotely verified free.

## Current State

Cycle 0 documentation is drafted under the verified Dashboard lock. No implementation file has been created.

## Next Exact Action

Add failing tests for immutable domain models, validation, JSON round-trip, progress invariants, and explicit final-result semantics; run them to capture the expected red state before implementing `models.py`.

## Blockers

None for the isolated port foundation. Production integration remains intentionally deferred until the dependent cores publish accepted contracts.
