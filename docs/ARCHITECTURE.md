# Architecture

## Modules

- `journal_factory.config`: default paths and run configuration.
- `journal_factory.preflight`: mandatory file discovery and build blockers.
- `journal_factory.ingest`: ZIP/DOC/DOCX inventory and article candidate detection.
- `journal_factory.template`: DOTX/DOCX style snapshot extraction.
- `journal_factory.docx_builder`: draft journal assembly from ETALON/template styles.
- `journal_factory.audit`: per-article text/object audits and release gate.
- `journal_factory.llm`: local LLM client abstraction with offline fallback.
- `journal_factory.webapp`: browser admin panel and JSON API.
- `journal_factory.cli`: command-line entrypoint.

## Build Flow

1. Preflight checks mandatory sources.
2. Archive inventory extracts candidate articles without copying failed journals.
3. Template snapshot records style names and basic formatting.
4. Journal draft is assembled from the ETALON document and candidate article text.
5. QA reports are written as JSON and Markdown.
6. Release gate returns `PASS`, `FAIL`, or `BUILD BLOCKED`.

## Non-Negotiable Rule

The application must not claim a production-ready journal if the active `Журнал v3.2` skill, acceptance tests, QA schemas, or control journal v33 are missing.

