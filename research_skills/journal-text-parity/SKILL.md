---
name: journal-text-parity-research
description: Research-only corpus-grounded extension for proving RAW article-text parity against published NAUKAINFO conference PDFs. This skill never edits or replaces the verified journal skill automatically.
license: Proprietary project research skill
metadata:
  version: "0.2.0-research"
  status: "non-production"
  golden_target: "published Conference<ID>.pdf article regions"
  scope_excludes: "covers, service/front pages, table of contents"
---

# Journal Text Parity Research Skill

## Purpose

Recover and test the business rules that transform raw author submissions into the article text found in the published `Conference<ID>.pdf` files. The final PDF article region is the golden master. Raw files are immutable source evidence.

This research skill is an additive candidate only. Do not modify, replace, or silently extend the verified `skills/journal/SKILL.md` from corpus findings.

## Corpus snapshot

- Published PDF conferences: **83** (`53–75`, `78–137`).
- Conferences with supplied RAW material: **35**.
- Published article regions inside comparable conferences: **1,425**.
- RAW files inventoried: **3,398** supported candidates from **5,452** extracted files.
- Viable article-like RAW files after filtering: **2,191**.
- Article regions with a selected source match: **1,309**.
- High-confidence unique matches: **722**.
- Medium-confidence matches: **475**.
- Low-confidence matches: **112**.
- Unmatched comparable article regions: **116**.
- Median token recall among high-confidence pairs: **0.991509**.
- 10th-percentile token recall among high-confidence pairs: **0.977807**.
- Median token-order ratio among high-confidence pairs: **0.983501**.

These numbers are evidence about the current corpus and matcher, not a claim of 100% parity.

## Golden-target contract

For each published article:

1. Detect one article region in the final PDF using structural evidence, not page appearance alone.
2. Restrict RAW candidates to the same conference directory.
3. Exclude applications, forms, invoices, information letters, certificates, and other non-article material.
4. Deduplicate byte-identical RAW files before voting.
5. Select exactly one source version or return `BLOCKED`.
6. Compare article text only. Ignore covers, service pages, and TOC.
7. Separate editable editorial shell spans from protected author spans.
8. Classify every textual difference by an approved evidence-backed rule or return `BLOCKED`.

## Required worker roles

The orchestrator runs these logical workers. They may run as separate processes, jobs, or agents, but their outputs must be deterministic and mergeable.

### 1. `journal-inventory-worker`

One instance per conference. Produces PDF checksum, article-region inventory, RAW inventory, extraction failures, duplicate groups, and coverage statistics.

### 2. `raw-final-article-aligner`

One instance per article region. Scores title, author/header, body tokens, conference path, and source-version evidence. Outputs `MATCHED_HIGH`, `MATCHED_MEDIUM`, `MATCHED_LOW`, or `UNMATCHED`.

### 3. `article-text-fidelity-auditor`

Measures protected-body token recall, precision, canonical similarity, order preservation, paragraph provenance, additions, omissions, and suspected segmentation errors.

### 4. `editorial-span-boundary`

Marks ownership at span level:

- protected author wording;
- editable editorial metadata;
- mixed-ownership references;
- operator-only ambiguous content.

### 5. `corpus-rule-miner`

Aggregates proposed rules across journals. Every rule must include support count, applicable count, confidence, journal distribution, examples, and counterexamples.

### 6. `reference-dual-ownership-auditor`

Preserves reference wording and item order while independently testing editorial heading, numbering, and spacing.

### 7. `publication-text-regression`

Runs per-journal fixtures and release-blocking corpus thresholds. Critical failures cannot be averaged away by good scores elsewhere.

### 8. `provenance-ledger`

Maps each final protected span to source file SHA-256, source paragraph or run, final article ID, normalization profile, and approved rule IDs.

## Ownership model

### Immutable author-owned text

- title wording;
- annotation/abstract wording;
- keywords wording;
- article body;
- quotations;
- formulas represented as text;
- figure and table caption wording;
- reference wording and reference item order.

### Editorially mutable shell

- UDC/УДК insertion and placement;
- DOI/URL/ORCID label presentation;
- author-header layout;
- removal of contact data only when publication policy requires it;
- references heading and numbering presentation;
- article-boundary mechanics;
- whitespace and punctuation changes that do not alter protected wording.

### Operator-only decisions

- conflicting source versions;
- source article absent from the archive;
- content corrections;
- ambiguous article segmentation;
- low-confidence pairing;
- unclassified text insertion, deletion, or reordering.

## Corpus-derived candidate rules

Do not promote these automatically to production.

- `UDC_PRESENT_004` — **confirmed**, 722/722: every analyzed published article region begins with a UDC/УДК marker.
- `ARTICLE_BOUNDARY_007` — **confirmed**, 722/722: each article begins as an independent region and must not be concatenated to the previous article’s references.
- `REFERENCE_RESTART_005` — **confirmed**, 697/699: when numbered references exist, numbering normally restarts at 1; exceptions require explicit handling.
- `LABEL_SPACING_006` — **confirmed**, 466/499: `DOI:`, `URL:`, and `ORCID:` normally use a separating space; corpus counterexamples prevent blanket replacement without fixture tests.
- `TEXT_ORDER_002` — **probable**, 599/722: preserve article-word and paragraph order; reordering is not formatting.
- `CAPTION_SPACING_008` — **probable**, 157/190: figure/table abbreviation and number spacing follows recurring patterns, with counterexamples.
- `TEXT_PRESERVE_001` — **variable**, 226/722 under strict full-region comparison: this result shows that the current boundary/normalization model is not yet sufficient to treat all missing tokens as editorial loss.
- `HEADER_CONTACTS_003` — **variable**, 217/520: contact removal is conditional, not universal.

## Per-article evidence record

Each article result must contain:

- conference ID and article index;
- final PDF checksum and article page range;
- selected RAW path and SHA-256;
- duplicate/source-version group;
- match-score components and confidence;
- normalization profile ID;
- protected-body token recall and precision;
- token-order and paragraph-order metrics;
- added and removed token spans;
- editorial rule IDs applied;
- unresolved differences;
- final status and reason.

## Status model

- `PASS_EXACT`: one high-confidence source; protected text parity is exact after approved lossless normalization; no unclassified differences.
- `PASS_RULED`: one high-confidence source; every difference is covered by an approved editorial rule and provenance is complete.
- `REVIEW`: source is plausible but boundaries, source version, or differences require a person.
- `BLOCKED`: source missing, pairing ambiguous, low confidence, extraction failed, text changed without an approved rule, or provenance incomplete.

## Non-negotiable release gate

A journal may claim **100% article-text parity** only when all expected articles satisfy all of these conditions:

1. exactly one high-confidence RAW source match;
2. protected-body token recall `1.000000` after a documented lossless normalization profile;
3. protected token order and paragraph order preserved;
4. no unclassified additions, deletions, substitutions, or relocations;
5. every editorial difference references an approved rule with evidence;
6. complete span-level provenance;
7. zero `REVIEW`, `LOW`, `UNMATCHED`, or extraction failures.

The current corpus does **not** meet this gate. Therefore the current answer is `BLOCKED`, not “almost 100%”.

## Promotion policy

A research rule may be proposed for the verified skill only through a separate reviewed change containing:

- deterministic unit tests;
- per-journal regression fixtures;
- support across multiple journals;
- explicit counterexamples and exception behavior;
- proof that protected author text is not changed;
- rollback-safe implementation;
- no modification of the verified skill until review approval.
