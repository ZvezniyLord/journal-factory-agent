# JOURNAL_SKILL_V4_TWO_STAGE_DRAFT

Candidate MD logic for Journal Factory.

## What changed

1. ETALON first/last pages are opaque immutable zones and are outside runtime scanning/normalization.
2. The only write location is the exact `JOURNAL_CONTENT_SLOT`.
3. Slot sequence is fixed: conference TOC -> one page break -> draft article body.
4. Stage 1 copies articles one by one and changes only 11 pt / single spacing.
5. Stage 2 performs read-only technical segmentation and emits JSON.
6. Marker knowledge is based on measured corpus frequencies, not assumptions.
7. The active production release is not changed.

## Files

- `skills/journal/SKILL.md` — candidate master logic.
- `docs/JOURNAL_V4_TWO_STAGE_PIPELINE.md` — execution order.
- `docs/CORPUS_MARKER_ANALYSIS.md` — measured local corpus report.
- `schemas/template_shell_contract.schema.json` — immutable shell/slot contract.
- `schemas/article_technical_zones.schema.json` — per-article structure JSON.
- `data/structural_markers_v1.json` — marker frequency database.
- `examples/*.json` — valid examples.
- `tests/ACCEPTANCE.md` — acceptance rules.
- `ACTIVE_RELEASE_CANDIDATE.json` — candidate metadata only.

## Activation

Do not replace the current active skill or `ACTIVE_RELEASE.json` until the operator approves the candidate and the implementation has regression tests.
