# Core Development and Multi-Agent Coordination Protocol

## Purpose

This file defines the mandatory lifecycle for every current and future Journal Factory core and for all agent chats working in parallel.

## Codex local-workspace execution rule

This section applies specifically to Codex agents that have access to the user's computer, local repository, terminal, or mounted workspace.

Codex must treat the user's local working copy as the primary visible development workspace and GitHub as the shared coordination and publication repository. It must not silently perform the entire development cycle only inside an isolated cloud container when a usable local workspace is available.

Before claiming or implementing a core, Codex must:

1. locate and verify the user's actual local repository;
2. show the resolved repository path in its work report;
3. run `git fetch origin`;
4. verify the current branch and working-tree state;
5. update the local copy to current `origin/main` using a safe fast-forward operation, or stop with `BLOCKED` if local changes prevent a safe update;
6. verify that local `HEAD` equals the intended remote base before placing the lock;
7. perform the lock commit, push, fetch, and remote ownership verification from that local repository.

All implementation files, tests, fixtures, logs, reports, generated artifacts, and real-run evidence must be created or updated in the user's local working copy so the user can inspect them while the work is in progress. Codex must run focused tests, the full test suite, launch commands, smoke tests, and real-run checks on the user's computer or explicitly designated local environment whenever the required runtime is available there.

Codex must report the exact local commands executed, local paths used, test counts, failures, skipped tests, durations, generated artifact paths, and any processes started. Test evidence that exists only in an unobservable remote scratch environment is insufficient for acceptance when local execution is available.

After local verification succeeds, Codex must commit and push the approved implementation to GitHub. GitHub receives the reviewed local result; it is not a substitute for maintaining the user's local files.

If Codex does not have access to the user's local filesystem or terminal, it must say so before implementation and stop with `STATUS: BLOCKED — LOCAL WORKSPACE ACCESS REQUIRED`, unless the user explicitly authorizes remote-only execution for that task. It must not claim that the user's computer was updated, tested, or synchronized when it only worked in a cloud environment.

A local copy is considered synchronized only after Codex verifies both:

```text
git rev-parse HEAD
git rev-parse origin/main
```

and the expected commits are present locally. A successful GitHub push alone does not update the user's computer.

## Mandatory lock lifecycle

No implementation work may begin before the selected core is visibly claimed on current `origin/main`.

### Start of work

The agent must perform this exact sequence:

1. Fetch `origin/main` and fast-forward or rebase so the local branch is current.
2. Read `CORE_WORK_REGISTRY.yaml` completely.
3. Confirm that the selected core exists, is approved for the current phase, and has `in_progress: false`.
4. Set `in_progress: true` and fill `lock_owner`, unique `lock_session`, `claimed_at_utc`, `branch`, `work_item`, and exact `allowed_write_scope`.
5. Commit the registry claim as a separate commit.
6. Push the claim before editing implementation, tests, fixtures, API contracts, UI, passports, or development plans.
7. Fetch `origin/main` again.
8. Verify that the remote registry still contains this session as the owner.
9. Only after successful remote verification may the agent begin work.

A local edit, an unpushed commit, or a chat statement that work has started does not acquire the lock.

### End of work

The agent must perform this exact sequence:

1. Finish focused tests, full tests, real-run checks, artifact inspection, architecture review, and repository acceptance.
2. Commit and push all approved implementation work.
3. Fetch `origin/main` and verify that the same session still owns the lock.
4. Update the core record with `last_result`, `last_commit`, `completed_at_utc`, status, and notes.
5. Set `in_progress: false`.
6. Clear `lock_owner`, `lock_session`, `claimed_at_utc`, `branch`, `work_item`, and `allowed_write_scope`.
7. Commit the release as a separate final coordination commit.
8. Push the release.
9. Fetch `origin/main` again and verify that the remote registry contains `in_progress: false`.

Work is not considered closed until the release is visible on current `origin/main`.

## Reading and writing rules

- Every agent may read every core and every document.
- Only the verified lock owner may change a core or anything in its declared write scope.
- A second chat must not modify implementation, tests, fixtures, contracts, UI behavior, passport, or development plan belonging to a locked core.
- No agent may clear another session's lock without explicit user authorization.
- If ownership cannot be proven on current `origin/main`, the agent must stop with `BLOCKED`.

## Missing core registration

When the user names a core that is absent from `CORE_WORK_REGISTRY.yaml`, the agent must not start implementation immediately.

It must:

1. fetch current `origin/main`;
2. verify that no equivalent core or alias already exists;
3. add the core record with unique ID, aliases, phase, development case, dependencies, passport path, development-plan path, status, and `in_progress: false`;
4. commit and push that registration separately;
5. fetch again and verify the new record on remote main;
6. only then claim the core using the mandatory lock lifecycle.

## Core architecture separation

The following are separate cores and must not be collapsed:

- **Orchestrator Core** — deterministic conductor for core registration, dependency checks, routing, run state, transitions, invocation contracts, retries, pause/resume, failures, and action logging. It does not implement another core's domain logic.
- **Dashboard Core** — the operational execution center exposed through the browser. It receives paths and run parameters, starts or restores execution, requests work through ports, tracks every core, and presents progress, warnings, reports, files, and final results. It does not contain Excel parsing, matching, DOCX transformation, UDC detection, or LLM reasoning.
- **LLM Core** — a separate callable reasoning service. Other cores send a structured task, evidence, constraints, requested response schema, and confidence requirements. Model weights, runtime adapter, prompts, validation, retries, provenance, and structured responses belong only to the LLM Core. No other core may embed or invoke model weights directly.

HTML is an adapter and presentation layer. Business logic must not live in HTML.

## Mandatory core passport

Every registered core must have:

```text
cores/<core_id>/CORE.md
```

The passport must define:

- identity and aliases;
- business purpose;
- exact responsibility boundary;
- responsibilities explicitly excluded;
- inputs and outputs;
- ports, adapters, interfaces, and typed errors;
- dependencies and consumers;
- state and persistence ownership;
- deterministic rules and permitted LLM escalation;
- reports, logs, provenance, and audit requirements;
- security and data-integrity rules;
- acceptance criteria;
- known limitations and future extensions.

## Mandatory detailed development plan

Every registered core must also have:

```text
cores/<core_id>/DEVELOPMENT_PLAN.md
```

The plan must be created before implementation and must be derived from all relevant repository instructions, business documents, drafts, previous work, tests, and accepted decisions.

It must contain:

- inspected baseline and evidence;
- assumptions and open questions;
- architecture and domain model;
- file and module layout;
- staged implementation cycles;
- failing tests to create first;
- positive, negative, boundary, recovery, and integration cases;
- fixtures and real-run samples;
- migration and compatibility risks;
- observability and report fields;
- manual test procedure;
- completion checklist;
- completed items, current state, next exact action, and blockers.

A generic copied plan is forbidden. The plan must be specific to the selected core and updated after every completed cycle.

## Parallel-agent conflict prevention

Two or more chats may work simultaneously only when each owns a different registered core and the write scopes do not overlap.

Each lock must declare exact paths in `allowed_write_scope`. Broad overlapping scopes are forbidden.

Shared files include at least:

- `AGENTS.md`;
- `CORE_WORK_REGISTRY.yaml`;
- repository-wide configuration;
- dependency manifests;
- shared domain models;
- shared API contracts;
- root `index.html` unless ownership is explicitly assigned.

Before changing a shared file, the agent must fetch current `origin/main`, verify that no active lock owns the same file or contract, make the smallest possible change, commit it separately, push it, fetch again, and verify the remote result.

An agent must never replace a shared file using a stale local copy. After another chat pushes a registry or shared-file change, the next chat must fetch and integrate it before editing.

If scopes overlap or ownership is unclear, stop with `BLOCKED` until the user assigns ownership or creates a separate shared-contract work item.

## Interrupted work

An interrupted agent must not leave an unexplained lock. It must record `blocked` or `interrupted` with the reason and either retain or release the lock according to explicit user instruction.
