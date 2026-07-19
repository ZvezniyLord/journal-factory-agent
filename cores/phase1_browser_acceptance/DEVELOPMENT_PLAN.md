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

Registered and awaiting an atomic remote lock claim.

## Next Action

Push this registration, fetch and verify it, then claim `phase1_browser_acceptance` with an exact write scope before adding tests or implementation.
