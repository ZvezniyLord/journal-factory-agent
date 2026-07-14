# Skill map v3.1

## Discoverable skill

- `journal` → `skills/journal/SKILL.md`

## Internal modules

All prior `naukainfo-*` folders contain `MODULE.md`, not `SKILL.md`. They are implementation references routed by the master skill and are not independently activated.

## Critical routing

- source/body fidelity → `naukainfo-author-body-fidelity/MODULE.md`
- text diff → `scripts/deep_text_integrity_audit.py`
- media/object fidelity → `naukainfo-media-object-fidelity-gate/MODULE.md`
- shape/textbox/nested tables → `naukainfo-shape-textbox-nested-table-contract/MODULE.md`
- numbering → `naukainfo-numbering-definition-fidelity/MODULE.md`
- ETALON pagination → `naukainfo-etalon-section-pagination-fidelity/MODULE.md`
- references → `naukainfo-reference-block-fidelity/MODULE.md`
- TOC/free listeners → `naukainfo-toc-table-builder/MODULE.md`, `naukainfo-free-listener-toc-section/MODULE.md`
- final release → `naukainfo-quality-gate/MODULE.md`, `naukainfo-versioned-backup-release/MODULE.md`


## Priority order inside the master skill

- **Priority 0:** author-body lexical/structural/object fidelity and fail-closed deep audit.
- **Priority 1:** source/manifest/author/header/UDC correctness.
- **Priority 2:** ETALON insertion, canonical styles, pagination, tables/figures/references.
- **Priority 3:** TOC, render regression, release packaging and changelog.

- legacy DOC recovery → `naukainfo-legacy-doc-image-recovery/MODULE.md`
- TOC/body author synchronization → `naukainfo-toc-body-author-sync/MODULE.md`
