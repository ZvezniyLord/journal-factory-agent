# Мінімальний план інтеграції Agent Decisions

Щоб агент справді керував неоднозначними рішеннями, а не просив pipeline викликати іншу LLM, додайте один input-контракт.

## 1. CLI

Додати до `scan-conference` і `prepare-conference`:

```text
--agent-decisions <workspace/agent_decisions.json>
```

## 2. Пріоритет рішень

1. Валідувати decision bundle за JSON Schema.
2. Застосувати лише рішення, що посилаються на існуючий `source_file` та `excel_article_id`.
3. Не приймати рішення зі status `review` або confidence нижче policy threshold.
4. Потім запускати deterministic matching для решти.
5. Внутрішню LLM використовувати лише в transitional mode.

## 3. Типи рішень

- `article_match`: source file → Excel article ID.
- `service_file`: файл не є статтею.
- `header_labels`: індекси рядків → author/affiliation/title/unknown.
- `udc_suggestion`: код + confidence + evidence + operator review.
- `manual_exception`: документована причина продовжити/зупинити.

## 4. Audit trail

У `article_map.json` і `matches.json` додати:

```json
{
  "decision_source": "agent_decisions",
  "decision_id": "...",
  "agent_model": "...",
  "operator_approved": true
}
```

## 5. Тести

- invalid decision path rejected;
- decision cannot refer to absent Excel row;
- service file cannot also be matched;
- low-confidence UDC not inserted;
- deterministic result remains unchanged without bundle;
- raw root and ETALON hashes remain unchanged.


## 6. Table-format fidelity gate

Після normalizer та після вставки статті у master shell додати окремий детермінований gate:

1. Отримати source article copy і target journal copy.
2. Зіставити таблиці за порядком/структурою та точним текстом клітинок.
3. Обчислити effective paragraph formatting через direct property і style/base-style chain.
4. Якщо source effective first-line indent = 0, а target успадкував ненульове значення від ETALON `Normal`, записати прямий zero override тільки в table paragraphs.
5. Повторно відкрити DOCX і вимагати zero unexplained table differences.
6. Перед quality gate виконати full render review; сторінки з таблицями є mandatory checkpoints.

Інтеграційні тести:

- target `Normal` firstLine=567 не повинен змінювати table text placement;
- global `Normal` і service/body paragraphs залишаються незмінними;
- source/target cell text, runs, alignment і spacing збігаються;
- merged-table mismatch блокує автоматичний fix;
- після fix save/re-open audit повертає `pass`.


## Semantic style-routing stage

Add a deterministic stage after article insertion and before pagination/TOC finalization. It must classify paragraph roles, emit a JSON role map, apply narrow zero-indent overrides, preserve numbering/hanging geometry, then run table and visual audits. Style assignment is allowed only from the ETALON role map and only after outline/TOC side effects are validated.

## Shape fidelity stage

During scan, record SmartArt/textbox/shape counts and signatures. After insertion, validate diagram data/drawing relationships and repair only exact source-target matches. Any ambiguous or dependent shape package stops the build for operator review.


## Canonical section and style application (v1.5)

- Section headings in the journal body are English-only, resolved by `section_id` from the official project section library, inserted once before the first article of a non-empty section, and styled `SECTION`.
- For the Hnysiuk article in conference 136, section 1 is verified as `ECONOMIC THEORY, MACRO- AND REGIONAL ECONOMY`.
- The final DOCX must contain actual style IDs: DOI/UDC=`UDC`, human names=`AUTOR`, author metadata=`pip`, title=`Назва1`, drawing paragraph=`РИС`, figure caption=`РисПід`, table cells=`TABLETEXT`, reference heading=`REF-TITLE`, reference entries=`REFER`.
- A visually similar result with `Normal` style is a build failure. Style assignment is followed by reopen audit and full render.

## Table/figure caption normalization stage (v1.6)

After canonical style routing and before pagination:

1. Classify table number, table title, source note, drawing paragraph and figure caption.
2. Apply controlled direct formatting to table number/title and actual styles `TABLETEXT`, `РИС`, `РисПід` to verified roles.
3. Preserve table structure, cell alignment/emphasis and drawing relationships.
4. Reopen, audit first-line indents/style IDs, then render every affected page.

Integration tests must reject positive cell/caption first-line indents, displaced captions, missing object relationships and table-title/table separation.

## Reference-block normalization stage (v1.6)

Before pagination/TOC finalization:

1. Replace Ukrainian heading variants with `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`.
2. Enforce one blank before and none after the heading.
3. Apply `REF-TITLE` and `REFER` actual style IDs.
4. Create a fresh per-article numbering instance based on the ETALON reference abstract numbering and restart at 1.
5. Remove copied direct indents/tabs and foreign numbering that override the 567-twip hanging geometry.
6. Reopen and render reference pages; any bullets/arrows, continued numbering or misaligned continuation lines block the quality gate.


## v1.7 layout/style correction note

After applying canonical article styles, run the spacing/TOC gate: add required blank paragraphs after article titles, after figure/table/source blocks, before and after the reference stamp, and ensure only `SECTION`, `AUTOR`, and `Назва1` can feed the TOC. Clean reference runs equivalent to Word `Ctrl+Space` before applying `REFER` numbering.


## v1.8 multi-article integration

Pipeline stage order for multi-article drafts: validated single-article copies → semantic range extraction → relationship-preserving composition → article-start break normalization → per-article reference restart → structural/content/object audit → first render → TOC page materialization → final render/quality gate. `numId` values from input articles are never trusted after composition.


## v1.9 semantic preflight

Pipeline order: authoritative `Jurnal.dotx` style import → UDC presence/lookup gate → author-header contact/grammar cleanup → canonical title/front-matter styles → annotation/keywords normalization → body/table/shape normalization → reference boundary reconstruction → URL/DOI labeling + Ctrl+Space-equivalent rebuild → fresh per-article numbering → structural/content/media QA → full render review.

## v2.0 integration requirement: immutable author body

Add `audit_author_body_fidelity.py` before normalization, after single-article formatting, after multi-article merge and before finalization. Store the report in the build audit bundle. Manual body lists must retain their original representation; reference lists are processed separately.


## v2.2 TOC/front-matter update
- TABLE OF CONTENTS is a real 3-column Word table, not loose paragraphs.
- TOC generation scans canonical styles only: `SECTION`, `AUTOR`, `Назва1`; output styles are `Tab_SEC`, `Tab_PIP`, `Tab_Taitl`.
- Article front matter is normalized to DOI/UDC -> author header -> one blank -> title -> one blank -> body.
- Split source titles are merged; duplicate title paragraphs created by the builder are prohibited.
- Page numbering from ETALON must be preserved by keeping the numbered middle section break before the final service page.


## v2.5 full-release TOC author/page rule

For full journal releases, the TOC is generated only after rendering and page detection that excludes TOC-title occurrences. TOC author cells use a cleaned author map and may contain only participant names. Roles, institutions, degrees, ORCID, locations and contacts must not leak into TOC author cells.

## v2.9 integration tasks

- Call `recover_legacy_doc_images.py` only when source-render evidence shows converter loss.
- Persist per-article media hash/order signatures in the manifest.
- Centralize marker classification through `normalize_multilingual_markers.py`.
- Run `audit_media_content_hashes.py` and `audit_toc_author_sync.py` before finalize.

## v3.0 implementation order

Integrate `finalize_journal_v32.py` logic into the deterministic builder only after source/article range identification. Run ETALON section signature checks before and after writing, then object completeness, reference inference, listener TOC synchronization, and two-pass rendering.
