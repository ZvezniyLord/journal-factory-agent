# Hermes Multi-Chat Task Handoff Protocol

## Purpose

This repository is the persistent team memory for the Hermes project. A new chat must behave as a new team member, not as an isolated assistant and not as a prompt generator.

Chat history is optional context. The current GitHub repository state is the source of truth.

## Mandatory behavior for every new Hermes chat

Before proposing implementation, commands, architecture, or a task for another chat, the agent must:

1. Open and read `AGENTS.md` completely.
2. Fetch the latest `origin/main` and inspect the latest commits.
3. Read `CORE_WORK_REGISTRY.yaml` completely.
4. Read the mandatory documents routed by `AGENTS.md`.
5. Inspect existing core locks, branches, task briefs, passports, plans, and active work.
6. Continue from the latest committed state instead of recreating prior decisions from chat text.

## When the user asks to prepare work for another chat

A request such as "дай команду третьому чату", "підготуй чат для LLM", or "створи завдання іншому агенту" is a repository coordination task.

The coordinator must not merely print a long prompt into the chat window.

The coordinator must, when repository write access is available:

1. Fetch and verify current `origin/main`.
2. Resolve the requested work to a registered core.
3. If the core does not exist, register it first with `in_progress: false`, aliases, phase, dependencies, passport path, development-plan path, and proposed write scope.
4. Create or update the core passport and detailed development plan only through the correct coordination scope.
5. Create a dedicated task branch from the latest verified base, using a clear name such as `task/llm-core-<work-item>`.
6. Create a persistent task brief at `tasks/<task-id>.md` containing the objective, target core, branch, allowed write scope, dependencies, exclusions, required tests, acceptance criteria, current repository commit, and exact first action for the receiving chat.
7. Commit and push the task brief and branch so the next chat can discover them.
8. Do not claim the implementation lock on behalf of a chat that has not started work. The receiving chat must acquire and remotely verify its own core lock before implementation.
9. Return only a short handoff message naming the branch and task brief path.

If repository write access is unavailable, the agent must say so plainly and provide the smallest possible bootstrap instruction that tells the receiving chat to open `AGENTS.md`; it must not invent completed repository actions.

## Receiving-chat protocol

The receiving chat must:

1. Open `AGENTS.md` and follow the complete reading chain.
2. Fetch `origin/main` and the assigned task branch.
3. Read the task brief, registry record, passport, and development plan.
4. Verify that the task is still current and that its write scope does not overlap another active core.
5. Acquire the core lock itself: mark `in_progress: true`, fill owner/session metadata, commit, push, fetch, and verify ownership on the remote.
6. Begin implementation only after remote lock verification.
7. Push implementation results.
8. Record the result, release the lock, commit, push, fetch, and verify that `in_progress: false` is visible remotely.

## Conflict prevention

- One implementation chat owns one core lock.
- Different chats may work in parallel only on different cores with disjoint write scopes.
- A task branch is not a lock.
- A task brief is not a lock.
- A local commit is not a lock.
- A chat message saying "I started" is not a lock.
- Only a pushed and remotely verified registry claim is a valid lock.
- Shared coordination files must be edited from a freshly fetched base and pushed as small isolated commits.
- No chat may overwrite a newer registry, passport, plan, task brief, or shared contract with a stale local copy.

## Minimal task brief template

```markdown
# Task: <title>

- Task ID: <stable-id>
- Target core: <core-id>
- Base commit: <sha>
- Task branch: <branch>
- Status: prepared | claimed | blocked | completed
- Prepared by: <chat/session>
- Prepared at UTC: <timestamp>

## Objective

## Repository context

## Allowed write scope

## Forbidden write scope

## Dependencies

## Required passport and plan updates

## Required failing tests

## Required real-run verification

## Acceptance criteria

## Exact first action for receiving chat

Open `AGENTS.md`, follow the mandatory reading chain, fetch this task branch, then acquire and remotely verify the target core lock before editing implementation files.
```

## User-facing behavior

After preparing a task in the repository, the coordinator should respond briefly, for example:

```text
Завдання підготовлено в гілці `task/llm-core-runtime`.
Інструкція для третього чату: `tasks/llm-core-runtime.md`.
Нехай чат відкриє `AGENTS.md` і виконає task brief; lock він повинен поставити сам.
```

The repository record is the handoff. The chat message is only a pointer to it.
