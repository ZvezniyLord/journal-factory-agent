# GPT Classic

`GPT Classic` is the clean synchronization layer between the NAUKAINFO Google Drive factory and `ZvezniyLord/journal-factory-agent`.

Its immediate goal is to make the local/agent pipeline reproduce the **journal body** of the actually published Conference 136 and 137 releases while preserving all author text, tables, objects and captions.

Published-body parity starts at `TABLE OF CONTENTS` and ends after the last article reference block. Covers and service/front pages are treated as raw shell material and are excluded from this comparison. Image pixels are also excluded, while object presence, placement, dimensions, captions and pagination effects remain protected.

## Current focus

- complete TOC records with correct section, ordinal, full author list, comma separators and rendered page;
- special-thanks participants kept outside article numbering;
- corpus-driven author-header line composition instead of blind splitting or concatenation;
- exact continuation commas and spaces after `DOI:`, `URL:` and `ORCID:`;
- per-article reference numbering restart at 1 and compact published spacing;
- clean article boundaries with no `...pdfУДК` / `...URL:...DOI:` concatenation;
- caption punctuation such as `Рис. 1.`;
- per-article start-page tracking after TOC convergence;
- body-parity against Conference 136 and 137.

See `docs/PUBLISHED_REFERENCE_PARITY_136_137.md` and `skills/journal/SKILL.md`.
