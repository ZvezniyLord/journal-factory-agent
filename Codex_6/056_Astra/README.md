# 056 Astra — clean-room NAukaInfo journal factory

Public clean-room implementation workspace.

## If the local folder is only a normal folder, not a Git checkout

That is supported.

Default local target:

`X:\CODEX_5.5_redactor\Codex_6\056_Astra`

The repository branch remains the source of code/spec updates. The local folder can be synchronized without cloning the whole repository.

### One-shot sync + Hermes bootstrap

Run the public `REMOTE_BOOTSTRAP.ps1` from this branch, or download it and execute it.

It will:

1. download the current `astra/056-clean-room-skeleton` branch;
2. copy only `Codex_6/056_Astra` into the local target;
3. keep local `runs/` and `output/` state;
4. run the real local Hermes handshake.

The actual Hermes client/bootstrap code is in:

- `src/astra_journal/hermes_client.py`
- `src/astra_journal/bootstrap.py`
- `scripts/bootstrap_hermes.ps1`
- `scripts/sync_from_github.ps1`

## Read in this order

1. `LAUNCH_PROMPT.md`
2. `ASTRA_MASTER.md`
3. `EDITORIAL_RULES.md`
4. `HERMES_PROTOCOL.md`
5. `SKILL_INTEGRATION.md`
6. `naukainfo.yaml`
7. `config/hermes_runtime.json`

## Mandatory behavior

The implementation must connect to the real local Hermes runtime before finalizing its architecture plan.

Current validated local profile is defined in `config/hermes_runtime.json`.

Hermes is used for semantic workload and token/context economy.
Deterministic Python/OOXML/Word code remains the mutation and release authority.

## Clean-room rule

Do not inspect old project code outside this workspace.
Explicitly supplied old documents may be used as data/evidence only.
