# Corpus evidence — RAW submissions to published article text

## Scope

The published `Conference<ID>.pdf` article regions are the target. Covers, title/service pages, and table of contents are excluded. The source corpus is `Конференції.rar`.

## Verified corpus state

- 83 published PDF conference collections were downloaded and validated.
- IDs available: 53–75 and 78–137.
- RAW material maps to 35 conference IDs: 95, 96, 97, 98, 100–105, 107–115, 118–120, 122–127, 129–135.
- 5,452 files were fully extracted from the RAR.
- Two DOCX files with overlong archive paths were recovered by streaming their bytes to hashed safe paths.
- 3,398 supported source-document candidates were inventoried.
- 3,341 candidates yielded extractable text.
- 2,191 survived article-likeness filtering.
- 2,634 article regions were detected across all final PDFs.
- 1,425 article regions belong to conferences represented in the RAW corpus and are therefore directly comparable.

## Matching result

- 1,309 of 1,425 comparable article regions received one selected source candidate.
- 722 matches are high confidence.
- 475 matches are medium confidence.
- 112 matches are low confidence.
- 116 comparable final article regions remain unmatched.

Among high-confidence matches:

- median protected-region token recall: 0.991509;
- 10th percentile token recall: 0.977807;
- median token-order ratio: 0.983501;
- 75 near-exact cases;
- 316 minor editorial cases;
- 290 review/segmentation cases;
- 41 material-difference or suspected bad-match cases.

## Improvement over the first baseline

| Metric | Baseline | Corrected pass |
|---|---:|---:|
| Extracted RAW documents | 3,339 | 3,341 |
| Viable article-like documents | 2,775 | 2,191 |
| Any selected article match | 1,287 | 1,309 |
| High-confidence matches | 358 | 722 |
| Medium-confidence matches | 472 | 475 |
| Low-confidence matches | 457 | 112 |
| High-confidence median token recall | 0.989344 | 0.991509 |
| Near-exact high-confidence cases | 12 | 75 |

The improvement came from:

1. deriving conference ID only from the leading conference folder instead of every two/three-digit number in a path;
2. structural title detection near UDC and annotation blocks instead of accepting bibliography lines;
3. excluding non-article forms and administrative documents;
4. de-voting exact duplicate files;
5. hard same-conference candidate scoping;
6. selecting one source version per final article;
7. recovering the two overlong-path DOCX files;
8. reporting coverage only against the 35 conferences that have RAW material.

## Why the current skill cannot claim 100% article-text reproduction

1. **Source coverage is incomplete.** There are 116 comparable published article regions with no selected RAW source, and 48 published conferences have no supplied RAW conference directory.
2. **Only 722 article pairs are high confidence.** Medium and low matches cannot be used as release proof.
3. **Full-region token recall is below one for most pairs.** The present segmentation includes mixed editorial/header/reference spans and still needs stronger protected-span boundaries.
4. **Source-version ambiguity exists.** The archive contains duplicate, cleaned, corrected, and differently named versions; exact duplicates alone form many multi-file groups.
5. **Published text sometimes differs materially.** Forty-one high-confidence pairs are material differences or suspected bad matches, and 290 require review.
6. **References have dual ownership.** Wording/order are author-owned while heading/numbering/spacing are editorial; treating the whole block as one ownership class produces false failures or unsafe edits.
7. **Conditional practices were previously modeled as universal.** Contact removal, label spacing, caption spacing, and some reference behavior have counterexamples.
8. **The verified skill declares preservation but lacks a span provenance ledger.** It cannot currently prove which source paragraph produced each final protected span.
9. **One aggregate similarity score is unsafe.** A missing paragraph can be hidden by high similarity across a long article; critical gates must be independent.
10. **Rules based on only journals 136/137 overfit.** Cross-journal evidence shows confirmed, probable, variable, and exceptional behaviors.

## Strongly supported editorial rules

- UDC/УДК article-start marker: 722/722 high-confidence pairs.
- Independent article boundary: 722/722.
- References normally restart at 1: 697/699; exceptions c125-a014 and c127-a029.
- Spacing after DOI/URL/ORCID labels: 466/499; counterexamples exist.

## Probable or conditional rules

- Protected word/paragraph order: 599/722.
- Caption abbreviation/number spacing: 157/190.
- Header contact removal: conditional, 217/520.
- Strict full-region token preservation: unresolved under current boundaries, 226/722.

## Decision

The verified journal skill remains unchanged. Corpus findings are stored in a separate non-production skill. Promotion requires deterministic tests and explicit review of every exception class.
