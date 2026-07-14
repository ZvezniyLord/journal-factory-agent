---
name: naukainfo-conference-intake
description: Scans a conference Excel manifest and application folder, filters service documents, identifies probable articles, converts no files, and produces match candidates and readiness reports. Use for conference intake, scan-only, missing article investigation, or service-file classification.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Default mode: read-only scan

1. Call `scan_conference` with internal LLM disabled.
2. Read `scan_manifest.json`, `scan_files.json`, `scan_matches.json`, `scan_skipped_files.json`, `scan_summary.json`.
3. Verify Excel article count, probable files, matched, missing, duplicates and free listeners.
4. Service documents include applications, forms, receipts, payment confirmations and participant questionnaires. Do not classify solely by extension; inspect ambiguous DOCX content read-only.
5. Legacy `.doc` is reported as `requires_word` during scan; conversion happens only on a workspace copy during build.
6. For ambiguous candidates, activate `naukainfo-article-structure` and record explicit decisions in the decision bundle.

## Gotchas

- A multi-paragraph article title may be detected as only its first line.
- A free-listener form may contain a report title but is still not an article.
- File/folder names can be more reliable than a truncated title, but must not override Excel identity without evidence.
- Diagnostic build may intentionally continue with warnings to collect all errors; final build may not.

## Output

Use a table with Excel ID, authors, Excel title, candidate, detected title, score, decision and reason.
