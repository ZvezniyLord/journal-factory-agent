# 056 Astra — clean-room NAukaInfo journal factory

Public review skeleton for the new Codex 6 Astra implementation.

## Read in this order

1. `LAUNCH_PROMPT.md`
2. `ASTRA_MASTER.md`
3. `EDITORIAL_RULES.md`
4. `HERMES_PROTOCOL.md`
5. `SKILL_INTEGRATION.md`
6. `naukainfo.yaml`
7. `config/hermes_runtime.json`

## Mandatory behavior

Astra must connect to the real local Hermes runtime **before finalizing its architecture plan**.

It must:
- test the main Hermes endpoint;
- warm the model with a strict-JSON healthcheck;
- fall back to the CPU worker if needed;
- save the handshake;
- send its compact plan to Hermes for critique;
- incorporate valid suggestions;
- then continue implementation with Hermes as a semantic subagent.

Astra must not read old project code outside this workspace.
Explicitly supplied old documents may be used as data/evidence only.

## Workspace

All new implementation, tests, run state and outputs belong under this directory.
