---
name: naukainfo-journal-assembly
description: Builds a NAUKAINFO draft journal from validated article copies in Excel/section order using a copy of the master template. Use after scan and matching are understood, with explicit human approval for a full build.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Preconditions

- Preflight completed.
- Raw-root and ETALON hashes captured.
- Output is an isolated workspace.
- Diagnostic or production intent is explicit.
- Build approval token is available.

## Procedure

1. Call `build_journal` with `approval="BUILD_CONFIRMED"`.
2. Default to internal LLM disabled in agent-driven mode.
3. Use only a copied template.
4. Insert only non-empty official sections. Resolve each section from the validated section library, render its heading in English only, insert it once before the first article, and apply `SECTION`.
5. Insert articles in manifest order; each article starts on a new page.
6. Preserve the template’s covers, headers, footers, numbering and protected tail pages.
7. Activate `naukainfo-canonical-style-application` for every inserted article; actual ETALON style IDs are mandatory.
8. Do not perform a global style replacement that collapses author-specific visual semantics.
8. Record all created files and the exact command.

## Diagnostic build

A diagnostic build may continue with unmatched/needs-review items only after user confirmation. It must enumerate omissions and never be labeled final.

## Done when

A draft and all expected reports exist, source/template hashes are unchanged, and the artifact list is complete.
