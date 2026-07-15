# Journal Factory MVP

Local diagnostic MVP for inspecting author-submission archives and producing a
non-production DOCX text inventory draft.

## Current Status

This repository is not the production NAUKAINFO Journal Factory pipeline yet.
It does not execute the v3.5 skill modules for manifest ordering, TOC
generation, style routing, table/figure preservation, reference renumbering,
rendered PDF verification, or final production QA.

The current code can:

- run preflight checks for the source archive/folder, ETALON, template, and source pack;
- inventory DOC/DOCX submissions;
- extract text and write article audit reports;
- copy the ETALON and append a non-production text inventory draft;
- expose a local browser admin panel;
- fail closed when the MVP cannot prove production readiness.

## One-Button Start

```powershell
Set-Location 'C:\Users\Vint\Desktop\Галенко_Віталій_304ТН_варіант_5'
.\RUN_JOURNAL_FACTORY.ps1
```

This opens the launcher. Press `Start` to start Docker Compose where available,
start the local server, and open the browser at `http://127.0.0.1:8765`.

## Direct CLI

```powershell
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli preflight --source "N:\Конференції\136"
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli build --source "N:\Конференції\136"
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli serve --host 127.0.0.1 --port 8765
```

## Important Paths

- ETALON: `C:\Users\Vint\Desktop\ETALON-JOURNAL.docx`
- DOTX template: `C:\Users\Vint\Desktop\Jurnal.dotx`
- outputs: `build/`
- QA reports: `build/reports/`

## Release Gate

`PASS` is reserved for production-ready output. In the current MVP, unreadable
articles, missing UDC/reference markers, or unverified object fidelity prevent a
production pass. Generated DOCX output must be treated as an inspection draft
unless `build/reports/final_quality_gate.json` explicitly says:

```json
{
  "production_ready": true
}
```

