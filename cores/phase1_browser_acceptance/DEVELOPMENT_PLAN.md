# Phase 1 Browser Acceptance Development Plan

## Baseline

The operator rejected the root page because it only exposed an Orchestrator diagnostic menu. Existing Dashboard and Orchestrator foundations use explicit ports but have no production Workspace Driver or browser composition. The canonical acceptance archive is recorded in `docs/LOCAL_TEST_MATERIALS.md`.

## Scope

1. Capture the rejected page with real browser evidence.
2. Add failing tests for Workspace Driver invariants, API routes, visible controls, selection bridge, complete reports, structured failures, and state recovery.
3. Implement immutable workspace models, registries, port, filesystem adapter, and driver.
4. Implement a thin Phase 1 composition service that adapts Workspace Driver into Dashboard and Orchestrator contracts.
5. Implement loopback defaults, validate, create, status, selection, start, refresh, and resume APIs.
6. Replace `index.html` with the real operator interface and keep all path logic server-side.
7. Add a local launcher and document the exact command.
8. Run focused tests, full tests, the canonical archive run, JSON/JSONL inspection, browser checks, architecture review, and repository acceptance.
9. Push the implementation, synchronize the user-visible checkout, release the lock, and verify remote release state.

## Planned Modules

- `journal_factory/workspace_driver/`: contracts, models, registries, filesystem adapter, driver.
- `journal_factory/phase1_app/`: composition service, adapters, HTTP server, launcher.
- `tests/workspace_driver/`: domain and persistence tests.
- `tests/phase1_app/`: API, UI contract, integration, real-run, and artifact tests.

## Test Matrix

- explicit source normalization;
- explicit output override and Desktop default;
- missing and unsafe journal identifiers;
- files and directories as accepted source inputs;
- validation with no mutation;
- collision-safe repeated creation;
- canonical directory and report creation;
- absolute registry paths and registered report paths;
- action record for every creation step;
- typed filesystem failures;
- persisted status reconstruction;
- all browser controls and API routes;
- selection cancellation and dialog failure;
- invalid JSON and unknown run handling;
- no traceback leakage;
- start/refresh/resume with existing Dashboard and Orchestrator contracts;
- canonical archive path, size, hash, generated artifacts, and coherent references;
- desktop and 390-pixel browser layouts.

## Architecture Checks

- no workspace rule or absolute-path construction in HTML, HTTP controllers, Dashboard, or Orchestrator;
- no future core implementation;
- source remains unchanged;
- all dependencies enter through typed ports;
- persisted state reconstructs the UI after restart.

## Evidence

Acceptance evidence will be stored under `build/phase1_acceptance/` and excluded from Git. It will include screenshots, API captures, run inspection, source hash evidence, and server logs while remaining visible in the user's local repository.

## Current State

Implementation and local acceptance are complete. The prior diagnostic-only page is retained as failed baseline evidence under `build/phase1_acceptance/before/`. The replacement passed API, persistence, real-run, and browser checks.

## Next Action

Commit and push the verified implementation, synchronize the user-visible checkout, release the registry lock in a separate commit, verify remote ownership is free, and leave the local server running for the user UI check.

## Completed Work

- Added failing tests before implementation for missing Workspace Driver and Phase 1 application packages.
- Implemented source/output normalization, Desktop default, deterministic journal sanitization, pure validation, canonical layout, path/report registries, run context, action records, atomic reports, managed restore, and collision-safe unmanaged directories.
- Implemented persisted Dashboard state at the registered workspace report path and restart reconstruction.
- Adapted the released Dashboard and Orchestrator cores without modifying their implementation files.
- Added native archive/folder and output-folder selection APIs with structured cancellation/unavailable failures.
- Replaced the rejected root menu with editable paths, selection controls, journal review, server-computed workspace, Validate, Create workspace, Start run, Refresh, Resume, progress, core state, warnings, reports, and outputs.
- Added a loopback launcher and local run instructions.

## Verification Results

- Focused Workspace Driver suite: 10 passed, 0 failed, 0 skipped.
- Focused Phase 1 application suite: 6 passed, 0 failed, 0 skipped.
- Full suite: 66 passed, 0 failed, 0 skipped, warnings treated as errors.
- Canonical source: `N:\Конференції\Конференції_zip\95_м_Оксфорд,_Велика_Британія,_6_8_лютого_2026_року.zip`.
- Source size: 30,033,703 bytes.
- Source SHA-256 before and after: `d86c0c33b96b321f2980993ecc6f3f91d1d67dea1b5cb21588984ec581b0c2a2`.
- Real run: `succeeded_with_warnings`, 100% Dashboard progress, 41 coherent action records, 11 absolute canonical paths, six absolute existing reports, and `production_ready: false`.
- Browser automation called defaults, validate, create, start, refresh, and resume APIs and displayed all report/output paths.
- Edge screenshots: `build/phase1_acceptance/browser/desktop.png` and `build/phase1_acceptance/browser/mobile.png`.
- Browser layout: no horizontal overflow at 1440 or 390 pixels, all buttons fit, no running core remained at terminal state, and no error banner was present.

## Known Limitation

The source is registered as one selected Phase 1 asset and intentionally not parsed. The dashboard therefore reports `PASS WITH WARNINGS`; document processing and production readiness remain outside Phase 1.
