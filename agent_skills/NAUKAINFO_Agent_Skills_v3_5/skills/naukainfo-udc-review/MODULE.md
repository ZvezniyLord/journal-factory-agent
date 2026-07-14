---
name: naukainfo-udc-review
description: Detects a missing UDC, prepares a compact online classification request from title/abstract/keywords/section, requires evidence and operator approval, inserts the approved code with the canonical UDC style, and enforces exactly one blank paragraph after it.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; online-capable LLM/agent; NAUKAINFO Jurnal.dotx; MCP tools recommended.
metadata:
  author: naukainfo
  version: "2.1.0"
---

# Hard gate

- The gate runs **for every article in manifest order**, never once for the whole journal.
- Each article must contain exactly one literal `УДК ...` / `UDC ...` marker in its own frontmatter block. A UDC belonging to another article does not count.
- A `DOI:` line styled as `UDC` does not count; marker text and article-local position are mandatory.
- If an author-supplied UDC is present, preserve it. Never replace it automatically.
- If the target article lacks UDC, emit `UDC_LOOKUP_REQUIRED` and immediately run the online classification request. Missing detection or a missing generated proposal is `UDC_GENERATION_NOT_RUN`, not PASS.
- A documented high-confidence candidate may be inserted with `udc_source=generated`; ambiguous candidates remain blocked for operator review. The final field may never stay absent.

# Online lookup workflow

1. Select the target article by manifest ID/title and isolate only its frontmatter/body range. Collect the title, annotation/abstract, keywords and validated official section; add a short body excerpt only if needed.
2. Send that compact classification packet to an online-capable LLM/agent and require web research against authoritative/current UDC catalogues, library classifications or highly relevant indexed publications.
3. Return one primary candidate and up to three alternatives with:
   - exact `УДК ...` or `UDC ...` string;
   - topic reasoning;
   - evidence URLs/source names;
   - confidence;
   - `needs_operator_review: true`.
4. Store the proposal in `agent_decisions.json`. Insert a documented high-confidence candidate and tag `udc_source=generated`; otherwise require operator approval.
5. After approval, insert the UDC immediately after any DOI service line and before the author block.
6. Apply the exact authoritative template style `UDC`.
7. Insert **exactly one empty Normal paragraph after the UDC**—not zero and not more than one.

# Validation

- Enumerate every `Назва1` article title and assert exactly one article-local UDC marker before release.
- A global count of UDC-styled paragraphs is invalid evidence because DOI lines can share the style and other articles may already contain UDC.
- Run the gate before insertion, after assembly, and after save/reopen.
- UDC must not be inferred from years, page numbers or numbers in references.
- If authoritative evidence is unavailable or competing candidates remain close, defer to the operator.
- UDC/DOI paragraphs have no outline level and do not enter the TOC.
- After insertion, reopen and render the first article page.

# Decision contract

```json
{
  "type": "udc_suggestion",
  "article_id": "article-000",
  "title": "...",
  "section": "...",
  "udc": "УДК ...",
  "confidence": 0.0,
  "alternatives": [],
  "evidence": [{"source": "...", "url": "...", "note": "..."}],
  "needs_operator_review": true
}
```

Use `scripts/udc_lookup_request.py` to create the request packet and `scripts/insert_approved_udc.py` only after approval.
