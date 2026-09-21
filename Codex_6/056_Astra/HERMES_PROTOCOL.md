# HERMES_PROTOCOL.md
## Local Hermes semantic-worker contract

### 1. Role
Hermes is a local semantic worker for noisy source data.

**Hermes interprets. Astra decides and mutates.**

Hermes is not a DOCX editor and not a release authority.

## 2. Allowed Hermes tasks
Use Hermes for:
- classify file role: article / questionnaire / application / old_version / journal / cover / misc / garbage;
- extract probable title;
- extract probable authors;
- extract scientific supervisor;
- distinguish person vs institution;
- extract affiliation;
- detect probable UDC;
- detect probable DOI line;
- suggest thematic section;
- article ↔ questionnaire candidate matching;
- detect duplicates/alternate versions;
- classify bibliography continuation lines;
- analyze explicitly supplied old journals/articles as evidence;
- resolve ambiguous header-line roles;
- provide confidence + evidence.

Hermes should carry a large share of archive/document semantic scanning so Astra does not consume its own context reading hundreds of documents.

## 3. Forbidden Hermes tasks
Hermes MUST NOT:
- directly edit DOCX;
- write `document.xml`;
- choose/create `numId`;
- restart numbering;
- remap styles;
- merge relationships;
- mutate TOC;
- decide final Word formatting;
- rewrite scientific content;
- invent missing metadata;
- silently override Excel/article evidence;
- issue final PASS/BLOCKED verdict.

## 4. Input discipline
Core rule:

`ONE TASK -> SMALL INPUT -> STRICT JSON -> CACHE`

Never send:
- entire journal;
- entire archive;
- huge OOXML;
- dozens of full articles in one prompt.

Astra first extracts compact text/metadata.
Hermes receives only the material required for the current semantic task.

## 5. Configuration
External configuration only.

Suggested fields:
```text
HERMES_BASE_URL
HERMES_MODEL
HERMES_API_KEY
HERMES_CONTEXT
HERMES_TIMEOUT
HERMES_MAX_OUTPUT
HERMES_BATCH_SIZE
HERMES_CONFIDENCE_AUTO_ACCEPT
HERMES_CONFIDENCE_REVIEW
```

Support an OpenAI-compatible local endpoint.
Do not hardcode a model name.

## 6. Determinism
Where supported:
- temperature low / 0;
- strict JSON output;
- stable system prompt;
- schema validation;
- prompt versioning.

Cache key must include:
- SHA-256 of normalized input;
- task type;
- prompt/schema version;
- model id;
- relevant config hash.

## 7. Generic response envelope
Every Hermes task returns:
```json
{
  "task": "task_name",
  "status": "ok",
  "confidence": 0.0,
  "result": {},
  "evidence": [],
  "warnings": []
}
```

`confidence` is `0.0..1.0`.
No prose outside JSON.

## 8. Task: classify_file
Input:
```json
{
  "task": "classify_file",
  "file_name": "...",
  "relative_path": "...",
  "text_excerpt": "...",
  "metadata": {}
}
```

Result shape:
```json
{
  "file_role": "article|questionnaire|application|old_version|journal|cover|misc|garbage",
  "title": null,
  "authors": [],
  "supervisors": [],
  "affiliations": [],
  "udc": null,
  "doi": null
}
```

## 9. Task: extract_header
Input:
```json
{
  "task": "extract_header",
  "article_candidate_id": "...",
  "header_lines": ["..."],
  "format_hints": [
    {"line": 0, "bold": true, "centered": false}
  ]
}
```

Result:
```json
{
  "authors": [],
  "supervisors": [],
  "affiliations": [],
  "positions_degrees": [],
  "title": null,
  "udc": null,
  "doi": null,
  "contacts": []
}
```

## 10. Task: match_candidates
Astra computes a deterministic shortlist first.
Hermes receives only top candidates.

Input:
```json
{
  "task": "match_candidates",
  "registry_record": {
    "title": "...",
    "authors": ["..."],
    "section": "..."
  },
  "candidates": [
    {
      "file_id": "...",
      "title": "...",
      "authors": ["..."],
      "affiliation": "..."
    }
  ]
}
```

Result:
```json
{
  "selected_file_id": "...",
  "runner_up_file_ids": []
}
```

Final acceptance belongs to Astra threshold logic.

## 11. Task: classify_section
Use only when explicit registry section is unavailable.

Input:
```json
{
  "task": "classify_section",
  "title": "...",
  "udc": "...",
  "abstract_excerpt": "...",
  "allowed_sections": [
    {"id": "01", "name": "..."}
  ]
}
```

Return selected section id, confidence, evidence and alternatives.
Low confidence => review.

## 12. Task: classify_reference_continuation
Input:
```json
{
  "task": "classify_reference_continuation",
  "previous_reference": "...",
  "current_paragraph": "...",
  "next_paragraph": "..."
}
```

Result:
```json
{
  "is_continuation": true,
  "continuation_type": "url|doi|other|null"
}
```

Hermes never applies numbering.

## 13. Task: detect_duplicate_or_version
Use fingerprints + deterministic similarity first.
Hermes adjudicates only ambiguous cases.

Possible result:
- duplicate;
- alternate_version;
- unrelated;
- uncertain.

Never delete any file based only on Hermes.

## 14. Confidence policy
Suggested defaults:
- `>= 0.95`: eligible for automatic acceptance only if deterministic checks also agree;
- `0.80..0.949`: review/advisory;
- `< 0.80`: no auto-accept.

Thresholds are config.
Identity-sensitive cases require stronger deterministic agreement.

## 15. Batching
Batch only homogeneous compact tasks.

Good:
- 20 short file-name/excerpt classifications.

Bad:
- 20 complete DOCX article bodies.

Estimate request size and split before context pressure becomes dangerous.

## 16. Failure modes
Handle:
- timeout;
- HTTP 500;
- connection refused;
- invalid JSON;
- schema mismatch;
- truncated output;
- context overflow;
- empty response;
- low confidence;
- contradictory answers.

Required behavior:
1. bounded retry only for transient failures;
2. schema-validate every response;
3. never write an unvalidated response into authoritative manifest;
4. fall back to deterministic parsing where possible;
5. otherwise create a review item;
6. unresolved required identity/content item => BLOCKED.

Hermes failure must never corrupt a run.

## 17. Cache
Persist:
- request JSON;
- raw response;
- parsed response;
- schema version;
- model id;
- prompt version;
- cache key;
- timestamp;
- retry count.

Reuse cache only when hash/version/model/config identity matches.

## 18. Context-saving behavior
Astra must not keep raw Hermes results in active reasoning context.

Write to:
`runs/<run_id>/hermes/responses/*.json`

Then build compact:
- `source_index.json`;
- `matches.json`;
- `metadata.json`;
- `ambiguities.md`.

Continue from these structured files.

## 19. Auditability
Every accepted Hermes-assisted decision must be traceable to:
- request id;
- response id/cache key;
- confidence;
- evidence;
- deterministic signals;
- final Astra acceptance rule.

No invisible model decisions.

## 20. Security / privacy
Do not send data to a non-local endpoint unless explicitly configured by the operator.
Default expectation: Hermes endpoint is local.

## 21. Core invariant
Hermes may reduce Astra context use and manual semantic parsing.
Hermes may never become a hidden source of truth.
