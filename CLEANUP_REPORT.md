# Cleanup Report

Date: 2026-07-15

## Kept In Project Root

- `journal_factory/` - working MVP agent application
- `tests/` - project tests
- `docs/` - current project documentation
- `Dockerfile`
- `docker-compose.yml`
- `requirements.txt`
- `README.md`
- `RUN_JOURNAL_FACTORY.ps1`
- `RUN_JOURNAL_FACTORY.cmd`
- `ETALON-JOURNAL.docx`
- `Jurnal.dotx`
- `agent_skills/NAUKAINFO_Agent_Skills_v3_5/` - canonical v3.5 skills package from `E:\Downloads\NAUKAINFO_Agent_Skills_v3_5.zip`

## Moved To Quarantine

Path: `_quarantine/20260715_cleanup/`

Moved items include old nested repositories, generated build outputs, Graphify outputs, old local skill copies, IDE state, virtualenv, and generated logs.

The quarantine folder is intentionally ignored by Git and Docker. It can be deleted later after the clean project is verified and pushed.

## Git State

The project root was not a Git repository before cleanup. Nested repositories were preserved inside quarantine, not deleted.
