# Corpus marker analysis — local conferences 133, 136 and 138

## Scope

Analysis date: 2026-07-22.

The analysis used every conference corpus/release available in the current project workspace:

- Conference 133: 27 article units from the published reference PDF;
- Conference 136: 24 article units from the source archive;
- Conference 138: 28 article units from the source archive.

Total: **79 article units**.

Application forms, payment receipts and free-listener records without an article were excluded. Legacy DOC files were converted only to extract structural text markers. The analysis measures structure labels, not scientific meaning or document quality.

## 90% rule result

Only two multilingual marker families exceeded 90% in this local corpus:

| Tier | Marker family | Present | Frequency |
|---|---|---:|---:|
| A | UDC/УДК | 72/79 | 91.1% |
| A | references heading family | 74/79 | 93.7% |

The references family combines `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ`, `REFERENCES`, `СПИСОК ВИКОРИСТАНОЇ ЛІТЕРАТУРИ`, `СПИСОК ЛІТЕРАТУРИ`, `Liste der verwendeten Quellen`, and `Джерела`.

No other tested marker family reached 90%.

## Other measured families

| Tier | Marker family | Present | Frequency |
|---|---|---:|---:|
| B | Keywords / Ключові слова | 65/79 | 82.3% |
| B | Annotation / Abstract / Анотація | 61/79 | 77.2% |
| C | DOI | 38/79 | 48.1% |
| C | Table label | 19/79 | 24.1% |
| C | ORCID | 15/79 | 19.0% |
| C | Figure label | 14/79 | 17.7% |
| C | Conclusions / Висновки | 8/79 | 10.1% |
| C | Source note / Джерело | 3/79 | 3.8% |

## Design consequence

- UDC and references headings are strong deterministic anchors, but absence still must be reported rather than fabricated.
- Annotation and keywords are common supporting anchors, not mandatory blocks.
- DOI, ORCID, conclusions, tables, figures and source notes are optional. Their absence cannot be treated as an error.
- Header people/institution/position detection cannot rely on one universal label; it requires positional, lexicon, registry and corpus evidence.
- Percentages must be recalculated when new conference archives are added. The marker database is versioned and must keep corpus provenance.
