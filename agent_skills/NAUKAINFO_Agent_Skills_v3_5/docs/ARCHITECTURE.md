# Agent-first architecture

## Чому не треба переписувати Journal Builder

Наявний проєкт уже має сканування, matching, Word COM, normalizer, draft builder, audits і quality gate. Їх слід перетворити на **інструменти**, а не переносити бізнес-логіку в промпти.

## Шари

### 1. Agent host

Веде діалог, планує, обирає skill, викликає MCP tools, аналізує JSON і просить human approval.

### 2. Agent Skills

Містять доменні процедури, правила, gotchas, критерії stop/continue, формати звітів. Вони не повинні містити великий дубль Python-коду.

### 3. MCP adapter

Безпечні функції з чіткими JSON schemas. Він:
- викликає наявний `launcher.py`;
- контролює cwd, paths, timeouts;
- робить hashes до/після;
- не дозволяє output поверх source;
- вимагає approval token для build.

### 4. Existing project

Єдине місце фактичної DOCX/Excel business logic.

## Agent-driven ambiguous decisions

Цільова модель:

```text
scan deterministic → agent reads candidates/snippets → agent writes explicit decision bundle → validator checks bundle → pipeline consumes decisions → deterministic build
```

Це краще, ніж прихований nested LLM call усередині pipeline, тому що:
- рішення видно й відтворюється;
- можна змінити LLM host без зміни Python-коду;
- human review працює на рівні конкретного рішення;
- quality gate не залежить від моделі.

## Перехідний режим

Поки `--agent-decisions` не інтегровано, MCP tools можуть запускати наявний pipeline з внутрішньою LLM лише в явно зазначеному transitional mode. За замовчуванням внутрішня LLM вимкнена.


## Computed formatting boundary

DOCX business logic must distinguish direct OOXML properties from effective formatting. A missing direct `w:ind` can still render with an indent inherited from `Normal` or another base style. Therefore table fidelity is a deterministic project-layer concern: the agent selects the skill and reviews the report, while the script resolves style inheritance, writes narrowly scoped overrides, and leaves the master template style system intact.


## Semantic paragraph classification

Paragraph formatting is routed by semantic role rather than by blanket `Normal` normalization. The deterministic classifier owns role detection and narrow OOXML overrides; the agent reviews ambiguous classifications. This prevents service/caption/reference text from inheriting body indentation.

## Compound drawing object boundary

SmartArt and text-box fidelity belongs to the deterministic project layer because the visible object can span document.xml, diagram data/drawing parts, relationships and content types. The agent selects the skill and reviews rendered output; the script validates and repairs exact relationship mappings.


## Canonical section and style application (v1.5)

- Section headings in the journal body are English-only, resolved by `section_id` from the official project section library, inserted once before the first article of a non-empty section, and styled `SECTION`.
- For the Hnysiuk article in conference 136, section 1 is verified as `ECONOMIC THEORY, MACRO- AND REGIONAL ECONOMY`.
- The final DOCX must contain actual style IDs: DOI/UDC=`UDC`, human names=`AUTOR`, author metadata=`pip`, title=`Назва1`, drawing paragraph=`РИС`, figure caption=`РисПід`, table cells=`TABLETEXT`, reference heading=`REF-TITLE`, reference entries=`REFER`.
- A visually similar result with `Normal` style is a build failure. Style assignment is followed by reopen audit and full render.

## Caption and references deterministic boundary (v1.6)

Caption placement and reference numbering are deterministic project-layer concerns. Semantic role detection may be reviewed by the agent, but actual OOXML style assignment, `numId` creation/restart, direct-indent cleanup and spacing invariants must be performed by scripts and verified after save/re-open.

The reference appearance is a composition of paragraph style, numbering definition and direct properties. Therefore `p.style == REFER` alone is insufficient: the gate must also verify a fresh per-article `numId`, no conflicting direct `w:ind`/tabs, and the rendered 567-twip hanging alignment.


## v1.7 layout/style correction note

After applying canonical article styles, run the spacing/TOC gate: add required blank paragraphs after article titles, after figure/table/source blocks, before and after the reference stamp, and ensure only `SECTION`, `AUTOR`, and `Назва1` can feed the TOC. Clean reference runs equivalent to Word `Ctrl+Space` before applying `REFER` numbering.


## Multi-article composer boundary (v1.8)

The composer operates on semantic article fragments and imports complete OOXML relationships/media. A post-compose normalizer owns reference numbering, article-start page breaks, section-artifact removal and TOC timing. The LLM may choose order/section from the validated manifest but cannot alter source text or accept numbering continuation.


## v1.9 semantic normalization layer

Pipeline order: authoritative `Jurnal.dotx` style import → UDC presence/lookup gate → author-header contact/grammar cleanup → canonical title/front-matter styles → annotation/keywords normalization → body/table/shape normalization → reference boundary reconstruction → URL/DOI labeling + Ctrl+Space-equivalent rebuild → fresh per-article numbering → structural/content/media QA → full render review.

## Priority-0 integrity layer (v2.0)

Every stage consumes a raw semantic snapshot and emits a comparable signature. `naukainfo-author-body-fidelity` gates all transformations before assembly and after assembly. The pipeline is fail-closed when lexical body text changes or structural similarity falls below 99%.


## v2.2 TOC/front-matter update
- TABLE OF CONTENTS is a real 3-column Word table, not loose paragraphs.
- TOC generation scans canonical styles only: `SECTION`, `AUTOR`, `Назва1`; output styles are `Tab_SEC`, `Tab_PIP`, `Tab_Taitl`.
- Article front matter is normalized to DOI/UDC -> author header -> one blank -> title -> one blank -> body.
- Split source titles are merged; duplicate title paragraphs created by the builder are prohibited.
- Page numbering from ETALON must be preserved by keeping the numbered middle section break before the final service page.


## v2.4 full-release TOC author/page rule

For full journal releases, the TOC is generated only after rendering and page detection that excludes TOC-title occurrences. TOC author cells use a cleaned author map and may contain only participant names. Roles, institutions, degrees, ORCID, locations and contacts must not leak into TOC author cells.

## v2.9 fidelity pipeline

`source archive → immutable backup → source render/OLE inspection → semantic normalization → media relationship/hash audit → article assembly → final AUTOR/pip classification → TOC rebuild from body → render → page materialization → rerender → TOC/media/visual gates`.

## v3.0 structural safeguard

The document assembler must preserve ETALON body-level section properties and use paragraph `pageBreakBefore` for article boundaries. Media and nested shape/table traversal is per article. Listener records remain manifest-only TOC records and never enter article-body assembly.
