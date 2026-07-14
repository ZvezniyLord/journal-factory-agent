---
name: naukainfo-quality-gate
description: Aggregates NAUKAINFO audit reports and decides whether a diagnostic draft may proceed to finalization, with explicit human approval and no LLM override. Use after all structural and visual audits.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Gate inputs

- Excel reconciliation;
- text integrity;
- object integrity;
- section order;
- UDC/DOI/front matter audit;
- references audit;
- visual audit or an explicit statement that it is unavailable;
- operator actions;
- source/template immutability.

## Decision

- `blocked`: any critical issue or missing mandatory report.
- `review`: no critical issue, but manual actions remain.
- `pass`: all mandatory checks pass and operator approval is recorded.

## Hard rule

LLM output, confidence or agent reasoning cannot override a failed deterministic integrity check.

## Output

Return status, blocking issues, warnings, exact report paths, and the next permitted action. Do not silently finalize.
