---
name: naukainfo-preflight
description: Runs a safe readiness check for NAUKAINFO Journal Builder: unit tests, LLM endpoint smoke, template snapshot, source hashes, and environment checks. Use before scan, diagnostic build, full build, or code changes affecting pipeline behavior.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Procedure

1. Activate `naukainfo-project-context` first.
2. Call `run_unit_tests`.
3. Call `snapshot_inputs` for raw-root and template.
4. Call `template_snapshot` without modifying the template.
5. If a model is configured, call `test_llm_endpoint`; endpoint failure is reported, not hidden.
6. Return a preflight JSON summary with pass/warn/block.

## Blocking rules

Block when:
- template is missing;
- output resolves inside raw-root;
- output equals template path;
- unit tests fail in a critical module;
- source hashes cannot be captured for a write run.

Do not block a diagnostic run solely because matching is incomplete; clearly label it diagnostic and require approval.
