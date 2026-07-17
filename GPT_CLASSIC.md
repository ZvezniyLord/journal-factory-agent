# GPT Classic

`GPT Classic` is the clean synchronization layer between the NAUKAINFO Google Drive factory and `ZvezniyLord/journal-factory-agent`.

Its immediate goal is to make the local/agent pipeline reproduce the internal layout of the actually published Conference 136 and 137 releases while preserving all author text, tables, objects and captions.

The first-page cover and the visual pixels of author illustrations are excluded from style-parity scoring. Their existence, placement, dimensions, captions and effect on pagination remain protected by fidelity gates.

## Current focus

- publication manifest instead of inherited ETALON metadata;
- stale-template and placeholder blocking;
- complete numbered TOC with rendered page numbers;
- semantic author-header paragraph segmentation;
- per-article start-page tracking;
- final service-page isolation;
- conservative reference-label preservation;
- published-reference parity against Conference 136 and 137.

See `docs/PUBLISHED_REFERENCE_PARITY_136_137.md` and `skills/journal/SKILL.md`.
