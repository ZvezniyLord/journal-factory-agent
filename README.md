# Journal Factory

Local browser-driven Journal Factory, currently limited to the Phase 1 workspace and run-control workflow.

## Launch

From the repository root:

```powershell
python -m journal_factory.phase1_app.launcher
```

The launcher binds only to `127.0.0.1`, opens the root `index.html` through the local backend, and prints the active URL. If port `8765` is occupied, it selects an available loopback port.

## Test

```powershell
python -W error -m unittest discover -s tests -v
```

Phase 1 creates the canonical workspace tree and the required JSON, JSONL, and HTML reports. It does not parse or edit DOCX/Excel content, call an LLM, assemble a journal, render output, or claim production readiness.
