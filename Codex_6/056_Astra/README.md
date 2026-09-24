# 056 Astra — clean-room NAukaInfo journal factory

Public clean-room implementation workspace.

## Local folder

The actual local project folder currently used by the operator is:

`X:\CODEX_5.5_redactor\Codex_6\056_Asttra`

The double `tt` in `Asttra` is intentional for the existing local folder.  
The repository source path remains:

`Codex_6/056_Astra`

The local folder does not need to be a Git checkout.

## One-shot sync + Hermes bootstrap

`REMOTE_BOOTSTRAP.ps1` downloads the current public branch, copies only the repository workspace `Codex_6/056_Astra` into the local folder `056_Asttra`, preserves local `runs/` and `output/`, then runs the real Hermes handshake.

Implementation files include:

- `src/astra_journal/path_guard.py`
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

Hermes handles bounded semantic workload and saves Astra/orchestrator context.
Deterministic Python/OOXML/Word code remains mutation and release authority.

## Clean-room rule

Do not inspect old project code outside the local `056_Asttra` workspace.
Explicitly supplied old documents may be used as data/evidence only.
