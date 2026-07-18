# Iterative conference development protocol

## Objective

Develop one deterministic ruleset against Conference 95, then run the unchanged ruleset on 96, 97, and subsequent conferences. A conference-specific exception is never added silently: it requires a versioned rule, positive fixtures, counterexamples, and regression results for every previously processed conference.

## Cycle

1. Verify the RAW archive signature, SHA-256, path safety, symlinks, file count, uncompressed size, and expansion ratio.
2. Extract into a versioned workspace without changing the source archive.
3. Validate the official `Conference<ID>.pdf` using `%PDF`, page count, SHA-256, and a render probe.
4. Segment the golden PDF at article-level `UDC/УДК` markers.
5. Inventory and extract RAW DOCX/DOC/ODT/RTF/PDF/TXT files.
6. Exclude applications, receipts, invoices, certificates, and other non-article files using deterministic evidence.
7. Match each golden article to at most one RAW source using title, author, and bounded body evidence.
8. Return `MATCHED_HIGH`, `REVIEW`, or `UNMATCHED`. Unknowns are never converted to PASS.
9. Optionally ask a local LLM for a JSON suggestion on `REVIEW` items. The suggestion cannot produce PASS or edit article text.
10. Persist all artifacts, metrics, hashes, and blockers.
11. Run the same ruleset on the next conference and compare coverage and failure classes.

## Conference 95 acceptance fixture

- Official title: `OXFORD INTERNATIONAL SCIENCE FORUM`.
- Dates: February 6–8, 2026, Oxford, United Kingdom.
- ISBN: `978-617-8680-40-4`.
- Collection DOI: `10.64828/conf-95-2026`.
- Official PDF: 248 physical pages; bibliographic description: 245 pages.
- Expected article count: 34.
- First article printed start page: 6.

This fixture checks the parser. It does not permit copying old metadata into a new journal.

## Local commands

```bash
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt

python -m journal_factory.cli analyze-conference \
  --conference-id 95 \
  --raw input/95.zip \
  --golden input/Conference95.pdf \
  --expected-articles 34 \
  --output build/corpus_cycles
```

Windows one-command launcher after placing both files in `input`:

```powershell
.\RUN_CONFERENCE_95.ps1 -InstallDependencies
```

Custom paths are also supported:

```powershell
.\RUN_CONFERENCE_95.ps1 `
  -Raw "D:\JournalCorpus\95.zip" `
  -Golden "D:\JournalCorpus\Conference95.pdf"
```

Series regression:

```bash
python -m journal_factory.cli analyze-series \
  --manifest config/conference_series.json \
  --output build/corpus_cycles
```

Optional local Ollama/OpenAI-compatible review:

```bash
python -m journal_factory.cli analyze-conference \
  --conference-id 95 \
  --raw input/95.zip \
  --golden input/Conference95.pdf \
  --expected-articles 34 \
  --llm-endpoint http://127.0.0.1:11434 \
  --llm-model qwen3:8b
```

The LLM receives only the golden title/authors and the top three candidate paths with numeric scores. It never receives authority to rewrite the article, modify DOCX, or set PASS.
