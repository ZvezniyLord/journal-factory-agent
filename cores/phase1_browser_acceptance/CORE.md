# Phase 1 Browser Acceptance Passport

## Identity

- Core ID: `phase1_browser_acceptance`
- Phase: 1
- Type: narrow integration and acceptance work item
- Dependencies: Dashboard Core and Orchestrator Core

## Purpose

Deliver the first usable Journal Factory operator workflow at the root `index.html` while implementing the missing Workspace Driver boundary and composing existing Dashboard and Orchestrator capabilities behind loopback-only APIs.

## Ownership

This work item owns only:

- the root browser presentation and API client;
- Workspace Driver domain models, ports, filesystem adapter, service, and persistence;
- a Phase 1 composition root and loopback HTTP/selection bridge;
- a Windows/local launcher for that composition;
- focused integration, browser, real-run, and artifact-verification tests;
- its passport, plan, and generated acceptance evidence.

It may integrate with released Dashboard and Orchestrator public contracts. It must not change their internal domain behavior unless a newly discovered contract defect is separately coordinated.

## Boundaries

- HTML contains presentation, browser state, and API calls only.
- Workspace rules, sanitization, defaults, collision handling, path construction, and persistence live behind `WorkspaceDriverPort`.
- HTTP controllers translate requests and responses only.
- Native selection uses a loopback backend bridge and never trusts arbitrary browser filesystem access.
- Source archives are treated as immutable inputs.
- Phase 2 document discovery, Excel parsing, DOCX editing, LLM work, assembly, rendering, and document QA are excluded.

## Inputs

- source archive or directory path;
- optional output-parent path;
- operator-reviewed journal number;
- optional run ID for refresh/resume.

## Outputs

- validated configuration and server-computed workspace proposal;
- collision-safe canonical workspace;
- `run_manifest.json`, `action_log.jsonl`, `path_registry.json`, `report_registry.json`, and `run_summary.html`;
- persisted Dashboard state;
- browser-safe state, warning, report, and output references;
- typed errors without tracebacks.

## Interfaces

The Workspace Driver port exposes defaults, validation, creation, and status operations. The Phase 1 application port exposes native selection, workspace creation, run start, refresh, and resume. All records are immutable typed values at the domain boundary and JSON-safe values at the HTTP boundary.

## Failure Contract

Stable failures include invalid source, missing journal number, invalid output parent, unsafe path, collision or filesystem failure, missing run, invalid JSON, selection cancellation, and unavailable native dialog. Exceptions and tracebacks are never returned to the browser.

## Security And Integrity

- Bind only to `127.0.0.1`.
- Never modify the selected source.
- Never overwrite an existing run silently.
- Record absolute normalized paths and material actions.
- Use UTF-8 deterministic JSON and append-only JSONL.
- Do not call cloud services, Docker, or an LLM.

## Acceptance

Acceptance requires real API-backed controls for source, output, journal number, computed workspace, validate, create, start, refresh, and resume; visible existing report/output paths; coherent persisted artifacts from the canonical Conference 95 archive; desktop and mobile browser evidence; passing focused and full tests; repository acceptance; a pushed release; and a synchronized user-visible checkout.

## Limitations

The Phase 1 start action proves local workspace and orchestration plumbing. It does not process journal documents or claim production readiness.
