# Startup Asset Contract

## Purpose

This contract prevents a chat, agent, or application from inventing a journal when the production template is missing.

## Required folder layout

```text
JOURNAL_FACTORY_MASTER_v1/
  00_START_HERE/
  01_SKILL_JOURNAL/
  02_TEMPLATES_REQUIRED/
  03_REFERENCE_RELEASES/
  04_TECHNICAL_SPEC_FOR_APP/
  05_TESTS_QA_AND_SCHEMAS/
  06_SAMPLE_INPUT_ARCHIVE/
  07_OUTPUT_CONTRACT_AND_EXAMPLES/
  08_ARCHIVE_NOT_FOR_PRODUCTION/
```

## Blocking rule

No ETALON = no build. No Jurnal.dotx = no build. No manifest = no build. No master skill = no build.

Never create a replacement cover, TOC, style set, sections, footers, or page numbering from a blank document. Work only in a copy of `ETALON-JOURNAL.docx`.

## Reference release rule

`JOURNAL_136_FINAL_RELEASE_v33.docx` is used only for regression comparison. It is never a content source.

## Required result

A build may be released only after the per-article lexical/run/table/object audits, ETALON signature audit, final pagination/TOC rebuild, and full-page render inspection have passed.
