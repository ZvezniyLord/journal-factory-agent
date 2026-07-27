# Test plan — journal article-text parity

## Test levels

### A. Extraction tests

1. Extract DOC, DOCX, ODT, RTF, and TXT without altering source bytes.
2. Record a SHA-256 for every source file.
3. Recover overlong archive paths into safe hashed filenames while preserving the original archive path in the provenance record.
4. Fail closed on unreadable or password-protected article candidates.
5. Exclude forms, applications, invoices, certificates, information letters, and administrative templates from article candidates.

### B. Conference scoping tests

1. Derive the conference ID only from the leading conference directory.
2. Do not treat dates, submission numbers, phone fragments, or years as conference IDs.
3. Never pair a source from one conference with a final article from another conference.
4. Report final conferences that have no RAW directory separately from unmatched articles inside a comparable conference.

### C. Article segmentation tests

1. Detect article starts using UDC/УДК plus structural title/author evidence.
2. Exclude covers, service/front pages, and TOC.
3. Prevent the next article’s UDC/header from attaching to the previous article’s references.
4. Treat repeated UDC-like text inside article body as a possible false boundary and require corroborating evidence.
5. Emit start/end page and paragraph boundaries for every article region.

### D. Source-version tests

1. Group byte-identical files by SHA-256.
2. Detect cleaned/corrected/versioned filenames as competing versions.
3. Select no more than one source version per final article.
4. Return `BLOCKED` when the top two candidates are too close or conflict materially.
5. Preserve the complete candidate ranking in the audit record.

### E. Text-fidelity tests

For protected author-owned spans, independently test:

1. token recall;
2. token precision;
3. token order;
4. paragraph order;
5. exact quotations;
6. formula text;
7. caption wording;
8. reference wording and item order;
9. title, annotation, and keyword wording.

A high average similarity must not hide any missing paragraph or critical token span.

### F. Editorial-rule tests

Each rule requires fixtures for both successful cases and counterexamples.

- `UDC_PRESENT_004`: article begins with UDC/УДК.
- `ARTICLE_BOUNDARY_007`: article begins independently from previous references.
- `REFERENCE_RESTART_005`: numbering restarts at 1 except approved exception fixtures.
- `LABEL_SPACING_006`: DOI/URL/ORCID spacing, including known counterexamples.
- `TEXT_ORDER_002`: no unapproved token or paragraph relocation.
- `CAPTION_SPACING_008`: stable abbreviation/number presentation without caption-word changes.
- `HEADER_CONTACTS_003`: conditional contact removal only under an explicit publication-policy decision.

### G. Per-journal worker contract

For each comparable journal, create one report containing:

- expected article count;
- matched/high/medium/low/unmatched counts;
- extraction failures;
- source-version ambiguities;
- per-article status;
- rule applications;
- counterexamples;
- release status.

A journal is `PASS` only if every expected article is `PASS_EXACT` or `PASS_RULED`.

### H. Corpus release gates

All gates are independent and release-blocking:

1. Comparable article coverage = 100%.
2. Exactly one high-confidence source per article = 100%.
3. Protected token recall = 1.000000 for every article.
4. Protected token and paragraph order preserved for every article.
5. Unclassified differences = 0.
6. Extraction failures among expected source articles = 0.
7. `REVIEW`, `LOW`, and `UNMATCHED` counts = 0.
8. Every editorial rule has deterministic positive and counterexample fixtures.
9. Every final protected span has source provenance.
10. Verified journal skill remains unchanged unless a separate reviewed promotion PR passes all required tests.

## Current result

The corpus run is **BLOCKED for production promotion**:

- 1,425 comparable final article regions;
- 1,309 selected matches;
- 722 high-confidence matches;
- 475 medium-confidence matches;
- 112 low-confidence matches;
- 116 unmatched comparable articles;
- 331 high-confidence cases classified as review or material/suspected bad match;
- median high-confidence token recall 0.991509, not 1.000000.

This is a successful research run and an unsuccessful 100%-parity release test, which is the correct fail-closed outcome.
