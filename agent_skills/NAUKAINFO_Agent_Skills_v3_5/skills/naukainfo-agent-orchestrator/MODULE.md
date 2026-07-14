---
name: naukainfo-agent-orchestrator
description: Orchestrates an end-to-end NAUKAINFO journal run by selecting context, intake, article inspection, UDC review, normalization, assembly, DOCX audit, visual regression, quality gate, and memory skills. Use when the user asks to scan, build, test, diagnose, or finalize an entire conference journal.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.1.0"
---

# Workflow

Progress:
- [ ] Load project context
- [ ] Run preflight
- [ ] Scan conference
- [ ] Resolve ambiguous files/articles
- [ ] Create and validate decision bundle
- [ ] Present plan and request build approval
- [ ] Build on workspace copies
- [ ] Run DOCX/content/object audits
- [ ] Run visual regression
- [ ] Run quality gate
- [ ] Update project memory

## Routing

- Context/code question → `naukainfo-project-context`.
- Files/Excel/matching → `naukainfo-conference-intake`.
- Ambiguous DOCX/header/title → `naukainfo-article-structure`.
- Missing UDC → `naukainfo-udc-review`.
- Formatting copy → `naukainfo-minimal-normalization`.
- Table placement/source fidelity after ETALON insertion → `naukainfo-table-format-fidelity`.
- Paragraph-role and no-indent routing → `naukainfo-semantic-style-routing`.
- SmartArt/shapes/textboxes → `naukainfo-shape-object-fidelity`.
- Draft build → `naukainfo-journal-assembly`.
- Structural/content checks → `naukainfo-docx-audit`.
- PDF/JPEG comparison → `naukainfo-visual-regression`.
- Release decision → `naukainfo-quality-gate`.
- Lessons learned → `naukainfo-project-memory`.

## Plan-validate-execute

For every state-changing operation:
1. Produce a structured plan.
2. Validate paths, hashes and decision bundle.
3. Ask for approval.
4. Execute one stage.
5. Audit before continuing.

Do not collapse all stages into one opaque call.
