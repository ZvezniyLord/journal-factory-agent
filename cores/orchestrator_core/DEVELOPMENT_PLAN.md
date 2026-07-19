# Orchestrator Core Detailed Development Plan

## Inspected Baseline and Evidence

Inspected before implementation:

- `AGENTS.md` at `19488c8`;
- `CORE_WORK_REGISTRY.yaml` through registration commit `0edc8fe` and lock commit
  `b85be5d`;
- `docs/CORE_DEVELOPMENT_PROTOCOL.md`;
- `docs/NEW_CHAT_START.md`;
- all 1,038 lines of `docs/BUSINESS_LOGIC_AND_ROADMAP.md`;
- all 320 lines of `CODEX_INSTRUCTION.md`;
- `skills/repository_acceptance/SKILL.md`;
- clean canonical clone identity, branches, tags, tracked files, and remote state;
- the reset working tree and historical repository inventory without restoring any
  legacy MVP implementation.

Baseline facts:

- canonical remote is `ZvezniyLord/journal-factory-agent`;
- `orchestrator_core` was absent and was registered separately before lock claim;
- the remote lock belongs to session
  `orchestrator-core-20260719T202446Z-0edc8fe`;
- no current Orchestrator, Dashboard, LLM, Python package, test runner, or root
  `index.html` implementation exists;
- the Browser UI record is unlocked, and the user explicitly assigned only the
  initial root command menu to this work item;
- the Workspace Driver dependency is planned but not implemented;
- legacy code is evidence only and will not be restored or copied.

## Assumptions and Open Questions

Accepted assumptions for this cycle:

- The user's explicit request approves the Orchestrator foundation during Phase 1.
- Python 3 standard library is the minimal stack; no dependency manifest is needed.
- The Phase 1 action log adapter is in-memory. Production persistence will be
  injected through `ActionLogPort` by Workspace/Reporting work.
- One `advance` command handles one core plus its bounded retries, which makes
  cooperative pause deterministic and testable without threads.
- The root command menu demonstrates start and state only. It is not the Dashboard
  Core and owns no pipeline business rule.
- Run payloads are JSON-compatible opaque mappings.

Open questions deferred behind ports:

- durable snapshot format and Workspace Driver report key;
- timeout ownership between core adapter and Orchestrator;
- cancellation and operator approval state names;
- parallel DAG execution policy;
- API authentication if loopback-only deployment changes.

None blocks the deterministic single-process foundation.

## Architecture and Domain Model

The implementation uses ports and adapters:

```text
index.html -> local HTTP adapter -> OrchestratorPort
                                  -> Orchestrator
                                     -> CoreRegistry
                                     -> RunStateMachine
                                     -> CoreInvocationPort adapters
                                     -> ActionLogPort adapter

future LLM consumer -> LLMCorePort -> separate LLM Core adapter/runtime
```

Domain types:

- `RunState`
- `InvocationStatus`
- `FailureRoute`
- `CoreDescriptor`
- `RunRequest`
- `PauseRequest`
- `ResumeRequest`
- `CoreInvocationRequest`
- `InvocationError`
- `CoreInvocationResult`
- `RunSnapshot`
- `ActionRecord`
- `LLMTaskRequest`
- `LLMTaskResponse`

Services:

- `CoreRegistry`: registration and dependency graph rules;
- `RunStateMachine`: state graph and typed invalid-transition errors;
- `Orchestrator`: command handling, one-core advancement, retry/failure routing,
  pause/resume, snapshots, and action events.

Adapters:

- `InMemoryActionLog`;
- deterministic `SystemClock` and test clock;
- loopback `ThreadingHTTPServer` adapter;
- demonstration `CoreInvocationPort` used only by smoke/API launch.

## File and Module Layout

```text
cores/orchestrator_core/
  CORE.md
  DEVELOPMENT_PLAN.md
journal_factory/orchestrator_core/
  __init__.py
  contracts.py
  errors.py
  ports.py
  registry.py
  state_machine.py
  orchestrator.py
  adapters.py
  server.py
  smoke.py
tests/orchestrator_core/
  test_contracts.py
  test_registry.py
  test_state_machine.py
  test_orchestrator.py
  test_server.py
index.html
```

No Dashboard implementation directory, DOCX/Excel module, LLM runtime, Docker
configuration, dependency manifest, or shared business model will be created.

## Staged Implementation Cycles

### Cycle 0 - Passport and plan

- Create this passport and detailed plan before implementation.
- Commit them separately under the verified lock.

### Cycle 1 - Contracts, errors, registry, and state machine

Failing tests first, then minimal domain implementation:

- frozen/defensively copied typed contracts;
- core ID validation and duplicate rejection;
- unknown, self, and cyclic dependency rejection;
- legal and illegal state transitions;
- stable typed error codes.

Gate: focused Cycle 1 tests pass.

### Cycle 2 - Deterministic conductor

Failing tests first, then:

- begin and validate an ordered pipeline;
- invoke one registered core per `advance`;
- create deterministic request IDs;
- track completion and attempts;
- retry only typed retryable failures;
- route exhausted/terminal failure through all three policies;
- return immutable snapshots.

Gate: focused Orchestrator tests pass.

### Cycle 3 - Pause/resume and audit

Failing tests first, then:

- pause request for same active run;
- acknowledge pause before next invocation;
- reject wrong-run and illegal commands;
- resume exactly at the next uncompleted core;
- append sequence-ordered actions for commands, transitions, attempts, retries,
  warnings, and terminal outcomes;
- convert invocation-adapter exceptions to typed terminal failures without leaking
  traceback data.

Gate: recovery and action-log tests pass.

### Cycle 4 - Thin command menu and local adapter

Failing integration test first, then:

- serve root `index.html` on `127.0.0.1`;
- `GET /api/orchestrator/state`;
- `POST /api/orchestrator/start`;
- structured JSON errors and no traceback leakage;
- initial menu displays state, run ID, completed core count, action count, and
  warnings;
- no file selectors, Dashboard logic, domain parsing, or LLM logic.

Gate: real HTTP integration test passes.

### Cycle 5 - Full verification and release

- run focused tests;
- run full discovery suite;
- run the real smoke module on an ephemeral port;
- inspect returned HTML, JSON snapshot, action sequence, and shutdown;
- scan for forbidden imports and out-of-scope changes;
- perform repository acceptance;
- update this plan with actual evidence;
- push implementation, record result, and release the lock separately.

## Failing Tests to Create First

- duplicate core ID returns `CORE_ALREADY_REGISTERED`;
- malformed core ID returns `CORE_ID_INVALID`;
- missing dependency returns `CORE_DEPENDENCY_UNKNOWN`;
- cyclic dependency returns `CORE_DEPENDENCY_CYCLE`;
- empty and duplicate pipelines are rejected;
- a consumer before its dependency is rejected;
- pre-satisfied dependency permits a consumer-only pipeline;
- invocation order matches requested order;
- retry succeeds on the final permitted attempt;
- retry exhaustion follows `fail_run`;
- terminal failure is never retried;
- `pause_run` stops before the next core;
- `continue_with_warning` completes with warnings;
- pause is acknowledged between invocations;
- resume continues at the exact next core;
- wrong run ID and illegal transition return stable errors;
- adapter exception becomes `CORE_INVOCATION_EXCEPTION` result data;
- actions are append-only and monotonically sequenced;
- HTML loads and contains the start command/state region;
- API state is initially idle and start reaches completed;
- unknown routes and malformed JSON return structured errors without tracebacks.

## Test Matrix

Positive cases:

- single-core success;
- dependency-ordered multi-core success;
- pre-satisfied external dependency;
- retryable failure followed by success;
- pause, resume, and completion;
- continue with warning;
- loopback HTML/API smoke.

Negative cases:

- invalid/duplicate/unregistered core;
- missing/cyclic/self dependency;
- empty/duplicate/misordered pipeline;
- begin while active;
- pause/resume with wrong run ID;
- resume outside paused state;
- permanent failure;
- malformed result returned by an adapter;
- malformed API JSON and unknown API path.

Boundary cases:

- zero retries;
- maximum configured retry count;
- one-core pipeline;
- dependency satisfied outside the pipeline;
- pause requested after the final invocation;
- payload remains unchanged after invocation;
- warning completion with one failed and one successful core.

Recovery cases:

- invocation adapter raises an exception;
- failure route pauses and resume retries no already completed core;
- pause request is idempotently rejected after acknowledgement;
- terminal snapshot remains stable under repeated reads.

Integration cases:

- real `ThreadingHTTPServer` bound to loopback and ephemeral port;
- GET root, GET initial state, POST start, GET terminal state, clean shutdown;
- HTML uses only the documented API and contains no business routing table.

## Fixtures and Real-Run Samples

No user documents or network fixtures are needed.

Test fakes:

- `ScriptedCore` returning a declared result sequence;
- `RaisingCore` for adapter exception conversion;
- fixed UTC clock;
- in-memory action log.

Real smoke sample:

- deterministic registered core `bootstrap`;
- run ID generated by the HTTP adapter;
- one opaque operation `start`;
- terminal state `completed`;
- JSON smoke report printed to stdout;
- server uses port `0` and binds only to `127.0.0.1`.

## Migration and Compatibility Risks

- A future Workspace Driver may already define `RunContext` or `ActionRecord`.
  Integration must use adapters or an explicitly versioned shared contract, not a
  silent type replacement.
- Root `index.html` is shared with Browser UI/Dashboard work. This cycle keeps it
  minimal; later ownership must fetch and evolve rather than overwrite it.
- Namespace package layout must remain importable without adding a shared package
  initializer.
- Durable resume may require versioned snapshot migration.
- Changing state or error string values is a breaking API change.
- Retry policy must not migrate into domain cores or the future LLM Core.

## Observability and Report Fields

Snapshot JSON:

- `schema_version`, `run_id`, `state`, `pipeline`, `current_core`, `next_core`;
- `completed_cores`, `attempts`, `warnings`, `failure`, `pause_reason`;
- `revision`, `action_count`.

Action JSON:

- `schema_version`, `sequence`, `timestamp_utc`, `run_id`, `core_id`;
- `action`, `status`, `attempt`, `message`, `details`.

Invocation error JSON:

- `code`, `message`, `retryable`, `details`.

HTTP errors:

- `error.code`, `error.message`, `error.details`;
- never a traceback or exception representation.

## Manual Test Procedure

1. From the repository root run:
   `python -m journal_factory.orchestrator_core.server --port 8765`
2. Open `http://127.0.0.1:8765/`.
3. Confirm the command menu shows `idle` and zero completed cores.
4. Select **Start run** once.
5. Confirm state becomes `completed`, a run ID appears, completed cores is `1 / 1`,
   and action count is greater than zero.
6. Refresh the page and confirm the same terminal snapshot is restored from the
   running process.
7. Stop the server with `Ctrl+C`.

Expected result: no file chooser, article logic, Dashboard screen, LLM controls,
Python traceback, or external network request appears.

## Completion Checklist

- [x] Complete mandatory repository navigation.
- [x] Perform baseline repository acceptance audit.
- [x] Register `orchestrator_core` and verify it on remote main.
- [x] Claim only `orchestrator_core` and verify remote ownership.
- [x] Create the passport before implementation.
- [x] Create this detailed plan before implementation.
- [x] Add failing tests for contracts, registry, and state machine.
- [x] Implement contracts, registry, and state machine.
- [x] Add failing tests for conductor behavior.
- [x] Implement routing, retries, failure routes, and pause/resume.
- [x] Add failing HTTP/HTML tests.
- [x] Implement the thin adapter and root command menu.
- [x] Run focused and full automated tests.
- [x] Run and inspect the real smoke launch.
- [x] Perform architecture review and initial repository acceptance checks.
- [x] Update actual progress, evidence, next action, and blockers.
- [ ] Push implementation and verify remote state.
- [ ] Record result and release only the Orchestrator lock.

## Actual Progress and Evidence

Failing test evidence:

- `python -m unittest discover -s tests/orchestrator_core -p 'test_*.py' -v`
  initially ran five failed test-module imports because the intentionally absent
  `journal_factory.orchestrator_core` package did not exist.

Implemented under the declared scope:

- immutable structured invocation, action, snapshot, and future LLM contracts;
- stable Orchestrator errors;
- port protocols;
- core registry and deterministic dependency checks;
- legal run-state machine;
- conductor with ordered invocation, bounded retries, three failure routes,
  cooperative pause/resume, exception suppression, and append-only actions;
- in-memory and bootstrap smoke adapters;
- loopback HTTP state/start adapter;
- root command menu;
- 19 automated tests across contracts, registry, state, conductor, recovery, and
  real HTTP behavior.

Verification evidence:

- focused suite with `-W error::ResourceWarning`: 19 passed, 0 failed, 0 skipped,
  1.030 seconds;
- repository discovery suite: 19 passed, 0 failed, 0 skipped, 1.029 seconds;
- `python -m compileall -q journal_factory/orchestrator_core
  tests/orchestrator_core`: PASS;
- real `python -m journal_factory.orchestrator_core.smoke`: initial `idle`, final
  `completed`, `bootstrap` completed, six actions, 7,292 HTML bytes, clean server
  shutdown;
- live loopback launch: health and state endpoints returned valid JSON;
- completed-state browser artifact at 1280 x 800: run ID visible, state
  `COMPLETED`, `1 / 1` cores, six actions, zero warnings;
- mobile device-emulated artifact at 390 x 844: no clipping, overlap, or text
  overflow;
- scope/forbidden-import scan found no Dashboard implementation, LLM runtime,
  DOCX, Excel, cloud API, subprocess, public bind, or shell execution code.

User-visible local workspace evidence:

- resolved repository path:
  `C:\Users\Vint\Desktop\Галенко_Віталій_304ТН_варіант_5`;
- the checkout contained a pre-existing staged clean-reset change and could not be
  safely fast-forwarded without altering user work;
- only new Orchestrator scope paths and the current registry were mirrored into
  that checkout; representative SHA-256 hashes matched the canonical local clone;
- from that exact visible path, full discovery passed 19 tests with 0 failures and
  0 skipped in 1.032 seconds, compileall passed, and the real smoke reached
  `completed` with six actions and clean shutdown;
- no reset, stash, checkout replacement, or Dashboard path modification was used.

Architecture review:

- domain modules have no HTTP, filesystem, document, or model dependency;
- HTTP path resolution exists only in the static adapter;
- all core calls and action writes use injected ports;
- HTML contains only presentation and API commands;
- Dashboard Core remains separately locked by another session with disjoint paths;
- the LLM boundary is a protocol and structured contract only.

## Current State

Status: implementation and local verification are complete under the verified
lock. Initial architecture and artifact reviews pass.

Next exact action: fetch current remote main, integrate disjoint concurrent work,
rerun the combined full suite and smoke, commit/push the implementation, perform
final repository acceptance, then record the result and release the lock.

Blockers: none for the Orchestrator release. Strict branch synchronization of the
pre-existing dirty checkout remains a repository warning; its staged user work was
preserved and the approved Orchestrator files are present and locally verified.
