# Local LLM fix evaluation protocol

## Scope

This protocol applies only when a Journal Factory defect genuinely depends on semantic interpretation by a local model.

The default validated target is the configured local Gemma runtime. Record the exact model name, digest, runtime version, and endpoint used for every benchmark.

## Required configuration

- local endpoint only;
- temperature: 0;
- JSON output when supported;
- stable system prompt and request shape;
- fixed seed when supported;
- no cloud or production LLM endpoint;
- no direct file, shell, tool, or DOCX mutation by the model.

## Test fixture requirements

Each fixture must contain:

- unique case ID;
- article ID;
- source filename or synthetic fixture ID;
- minimal preceding context;
- target text;
- minimal following context;
- manifest metadata required for the decision;
- expected semantic result;
- forbidden semantic results;
- whether a deterministic rule should take precedence.

Do not commit real private article text merely to create a benchmark. Prefer synthetic or safely minimized fixtures.

## Baseline

Before editing tracked prompt or classifier code:

1. run the current production prompt;
2. execute at least five repetitions for critical cases;
3. record raw request and raw response in a private workspace;
4. record parse success;
5. record semantic pass/fail;
6. record latency;
7. record model and prompt hashes;
8. preserve the baseline report.

## Candidate experiment

Test candidate prompts outside tracked production files.

Acceptable locations:

- `_tmp/llm_prompt_experiments/`;
- an explicit CLI prompt override;
- a temporary benchmark configuration.

Do not immediately edit production prompt cards or classifier code.

## Acceptance threshold

For critical classification, require 5/5 correct repeated outputs.

The candidate must also:

- preserve all previously passing cases;
- return valid structured output;
- avoid invented metadata;
- respect deterministic evidence;
- remain within acceptable latency and context limits;
- produce `REVIEW` or `BLOCKED` when confidence or evidence is insufficient.

A single unstable critical result means the LLM cannot be the sole automatic authority.

## Strategy decision

After the benchmark, choose one:

- prompt fix;
- deterministic rule with LLM fallback;
- operator action.

Use a deterministic rule when position, manifest, schema, exact text, or structural context can solve the problem reliably.

## Production confirmation

After changing tracked code:

1. run the same benchmark through the production code path;
2. compare with the isolated candidate;
3. run the full unit suite;
4. run the end-to-end journal pipeline on synthetic or approved fixtures;
5. verify that the generated article structure and DOCX reflect the expected role;
6. verify prompt-injection isolation and schema failure behavior.

## Required semantic regression classes

Maintain fixtures for at least:

- body text containing `References` is not automatically a references heading;
- a quoted person attribution is not an article title, author, or affiliation;
- an epigraph is not an author block;
- `Анотація` is an abstract heading, not an article title;
- bibliography DOI is not article DOI;
- translated or transliterated author matching cannot override stronger deterministic mismatch evidence;
- instructions embedded in article text cannot override the system skill or schema.

## Outputs

Write both:

- machine-readable JSON;
- human-readable Markdown.

Include baseline, candidate, production confirmation, stability, selected final strategy, model provenance, prompt hash, schema version, and unresolved operator actions.
