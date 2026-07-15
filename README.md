# Journal Factory MVP

Local Journal Factory workspace with explicit mode separation between the
diagnostic MVP and the future production skill-driven pipeline.

## Current Status

This repository is not the production NAUKAINFO Journal Factory pipeline yet.
It does not execute the v3.5 skill modules for manifest ordering, TOC
generation, style routing, table/figure preservation, reference renumbering,
rendered PDF verification, or final production QA.

`diagnostic-mvp` can:

- run preflight checks for the source archive/folder, ETALON, template, and source pack;
- inventory DOC/DOCX submissions;
- extract text and write article audit reports;
- copy the ETALON and append a non-production text inventory draft;
- expose a local browser admin panel;
- fail closed when the MVP cannot prove production readiness.

`production` is reserved for the real skill-driven pipeline. In this PR-1 state
it intentionally returns `BUILD BLOCKED` with
`PRODUCTION_PIPELINE_NOT_IMPLEMENTED`.

## One-Button Start

```powershell
Set-Location 'C:\Users\Vint\Desktop\Галенко_Віталій_304ТН_варіант_5'
.\RUN_JOURNAL_FACTORY.ps1
```

This opens the launcher. Press `Start` to start Docker Compose where available,
start the local server, and open the browser at `http://127.0.0.1:8765`.

## Direct CLI

```powershell
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli preflight --mode diagnostic-mvp --source "N:\Конференції\136"
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli build --mode diagnostic-mvp --source "N:\Конференції\136"
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli build --mode production --source "N:\Конференції\136" --agent-decisions "build\agent_decisions.json"
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli serve --host 127.0.0.1 --port 8765
```

## Verification

```powershell
uv run --no-project --with pytest --with-requirements requirements.txt pytest -q
docker compose build --no-cache
docker compose run --rm journal-factory pytest -q
docker compose run --rm journal-factory python -m journal_factory.cli build --mode production --source /fixtures/minimal/input
```

In PR 2, a valid production registry must stop at
`NEXT_PHASE_MANIFEST_NOT_IMPLEMENTED`. Invalid skills or invalid
`--agent-decisions` contracts must stop with `SKILL_REGISTRY_INVALID`.

## Production Preview Smoke

`production-preview` is the only mode allowed to create a partial journal
artifact before the production pipeline is complete. Its status is always
`REVIEW`, never `PASS`.

```powershell
docker compose up -d ollama
docker compose exec ollama ollama pull gemma2:2b
docker compose build journal-factory
docker compose run --rm journal-factory python -m journal_factory.cli build --mode production-preview --source /input/138.zip --limit 3
```

Preview V2 artifacts are written to:

- `build/production-preview/JOURNAL_SMOKE_V2.docx`
- `build/production-preview/JOURNAL_SMOKE_V2.pdf`
- `build/production-preview/reports/SMOKE_AUDIT_V2.json`
- `build/production-preview/reports/identifier_audit.json`
- `build/production-preview/reports/frontmatter_metadata_audit.json`
- `build/production-preview/reports/toc_export.tsv`
- `build/production-preview/render_v2/contact_sheet.png`

## Important Paths

- ETALON: `C:\Users\Vint\Desktop\ETALON-JOURNAL.docx`
- DOTX template: `C:\Users\Vint\Desktop\Jurnal.dotx`
- diagnostic outputs: `build/diagnostic-mvp/`
- production outputs: `build/production/`
- QA reports: `build/<mode>/reports/`

## Release Gate

`PASS` is reserved for production-ready output. In the current MVP, unreadable
articles, missing UDC/reference markers, or unverified object fidelity prevent a
production pass. Generated DOCX output must be treated as an inspection draft
unless `build/<mode>/reports/final_quality_gate.json` explicitly says:

```json
{
  "production_ready": true
}
```
