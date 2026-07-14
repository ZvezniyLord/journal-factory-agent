# Implementation Plan

## Phase 1 - MVP

- Create clean repository structure.
- Implement strict preflight and blocker reporting.
- Inventory ZIP/DOC/DOCX input.
- Extract article text from DOCX files.
- Create DOTX style snapshot.
- Assemble an inspectable DOCX draft from ETALON.
- Write QA reports and release gate.
- Add regression tests for blockers and article detection.

## Phase 2 - Word Fidelity

- Add Word COM/LibreOffice rendering adapter.
- Render every page to images/PDF.
- Verify TOC, pagination, headers, tables, pictures, formulas, and captions.
- Preserve every embedded object during normalization.

## Phase 3 - Operator Workflow

- Expand browser admin panel.
- Add manual correction queue.
- Add local LLM classification for ambiguous files and article blocks.
- Add acceptance-test runner and v33 control-journal comparison.

## Phase 4 - Release

- Enforce 100% acceptance pass.
- Produce final DOCX/PDF bundle.
- Export full QA evidence pack.

