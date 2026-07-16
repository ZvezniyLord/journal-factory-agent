# Journal Factory repository consolidation

## Decision

`ZvezniyLord/journal-factory-agent` is the consolidation target because it already contains:

- the canonical `journal` skill package version 3.5.0;
- the production skill registry and fail-closed contracts;
- the deterministic Journal Factory application;
- tests, Docker support, ETALON/template preflight, and production evidence manifests.

The repository may be renamed later, but another repository must not be created for the same product.

## Target layout

```text
.
├── AGENTS.md
├── .agents/skills/                  # repository workflows for coding agents
├── agent_skills/                    # versioned runtime journal skill bundle
├── journal_factory/                 # deterministic production application
├── tools/
│   └── graphify/                    # optional architectural-memory adapter
├── docs/
│   ├── architecture/
│   ├── migration/
│   ├── runs/
│   └── repository-consolidation.json
├── schemas/
├── tests/
├── fixtures/                        # synthetic data only
└── Dockerfile / docker-compose.yml
```

Do not keep a second `journal_factory` implementation under another nested project. Local-LLM code must be merged into the canonical package behind adapters and feature flags.

## Repository disposition

### Canonical

- `journal-factory-agent`
  - Keep.
  - Consolidation target.
  - Owns deterministic pipeline, runtime skill registry, QA, release gates, and operator UI.

### Migrate, then retire

- `NAUKA_iNFO_Jornal`
  - Import the reusable validated-fix workflow, fix protocol, LLM evaluation protocol, acceptance criteria, and any unique regression tests.
  - Do not import generated journals or private run artifacts.
  - Retire after imported content is verified in the canonical repository.

- `journal-factory-local-llm`
  - Merge unique adapters, schemas, prompt compiler behavior, security tests, and Docker/Ollama integration.
  - Keep deterministic code authoritative.
  - Remove duplicate pipeline and CLI implementations rather than nesting the entire repository.
  - Retire after parity tests pass.

- `journal-factory-graphify`
  - Import as optional developer tooling under `tools/graphify/` or retain as an external dependency if isolation is technically cleaner.
  - Production release decisions must not depend on Graphify.
  - Retire the standalone repository after the integration decision is documented and tested.

### Extract unique value, then archive

- `AIEditor`
- `Release-AI-Editor-5.5`
- `Release-AI-Editor-5.5-Public`
- `REDAKTTOR_1.0.5`
- `AI_redacktor`
- `AI_Redaktor`
- `Konvector_WORD`

Extract only:

- proven Word COM merge logic;
- article matching rules;
- DOC/DOCX/RTF conversion behavior;
- TOC and pagination logic;
- object-fidelity checks;
- regression fixtures that contain no private source material;
- design decisions that explain why the current pipeline behaves as it does.

Do not copy old GUI shells, virtual environments, build outputs, generated documents, duplicate dependencies, IDE metadata, local path catalogs, or obsolete pipeline copies.

### Unrelated repositories

Repositories for websites, bots, anti-detect browsers, unrelated publishing pages, or other products are outside this consolidation. They should be evaluated separately and must not be moved into Journal Factory merely to reduce repository count.

## Migration phases

### Phase 1 — inventory and freeze

1. Record every source repository default branch, latest commit, visibility, license, and unique responsibilities.
2. Mark source repositories read-only for the migration period.
3. Generate file inventories and checksums.
4. Identify secrets, private artifacts, generated outputs, model files, caches, and nested `.git` directories that must never migrate.

### Phase 2 — contracts and repository workflow

1. Add `AGENTS.md`.
2. Import and generalize the validated-fix repository skill.
3. Import fix and local-LLM evaluation protocols.
4. Add a machine-readable migration manifest.
5. Define ownership boundaries between deterministic code, local LLM decisions, operator review, and optional Graphify tooling.

### Phase 3 — local LLM merge

1. Inventory canonical and local-LLM modules by responsibility.
2. Keep one CLI and one `journal_factory` package.
3. Port only unique adapters and tests.
4. Preserve strict JSON schemas, prompt-injection isolation, model provenance, and fail-closed behavior.
5. Run raw-versus-skill-assisted benchmarks and full regression tests.

### Phase 4 — Graphify integration

1. Decide between an optional in-repo package and a documented external development dependency.
2. Preserve local-first privacy.
3. Add tests proving production builds do not require Graphify.

### Phase 5 — legacy extraction

1. Compare old editors against canonical modules.
2. Port only behavior that is both unique and proven.
3. Add a regression test before deleting duplicate code.
4. Record provenance and the source commit for every imported behavior.

### Phase 6 — retirement

A source repository is `safe_to_retire` only when:

- all unique files and behaviors have a recorded disposition;
- imported code has tests in the canonical repository;
- private artifacts were excluded;
- documentation links point to the canonical repository;
- the canonical branch is merged and green;
- a final archive/checksum exists when historical preservation is required;
- no active deployment, automation, local script, or user workflow still pulls from the source repository.

Prefer archiving for repositories with meaningful history. Delete only empty repositories, accidental duplicates, or repositories whose history has been deliberately preserved elsewhere.

## Immediate deletion policy

Do not delete any Journal Factory-related repository during Phase 1 or Phase 2. The current evidence is sufficient to identify duplicates, but not sufficient to prove that every unique implementation and private dependency has been preserved.

The first candidates for eventual deletion rather than archival are empty or accidental duplicates. Historical production repositories should normally be archived after migration, not erased.
