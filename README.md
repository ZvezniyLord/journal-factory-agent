# Journal Factory MVP

Local application for assembling a scientific journal from an archive of author submissions.

## Current Status

MVP is implemented with a strict preflight gate:

- required files are checked before any release build;
- missing mandatory requirements produce `BUILD BLOCKED`;
- archive inventory, DOC/DOCX detection, article audit, style snapshot, draft DOCX, QA reports, and release gate JSON are produced;
- the browser admin panel runs locally from the Python standard library.

## One-button start

```powershell
Set-Location 'C:\Users\Vint\Desktop\Галенко_Віталій_304ТН_варіант_5'
.\RUN_JOURNAL_FACTORY.ps1
```

This opens a small launcher window. Press `Start` to:

1. try to start Docker Desktop and `docker compose up -d`;
2. start the local server;
3. open the browser at `http://127.0.0.1:8765`.

You can choose either a ZIP archive or a folder as the input source.

## Direct CLI start

Use this when you want to run the pipeline manually:

```powershell
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli preflight --archive "N:\Конференції\136.zip"
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli build --archive "N:\Конференції\136.zip"
uv run --no-project --with-requirements requirements.txt python -m journal_factory.cli serve --host 127.0.0.1 --port 8765
```

## Important Paths

- source archive: `N:\Конференції\136.zip`
- ETALON: `C:\Users\Vint\Desktop\ETALON-JOURNAL.docx`
- DOTX template: `C:\Users\Vint\Desktop\Jurnal.dotx`
- outputs: `build/`
- QA reports: `build/reports/`

## Release Gate

`PASS` requires no critical preflight issues and no critical QA issues. If any mandatory file is absent, output is still generated for inspection where safe, but the release status remains `BUILD BLOCKED`.
