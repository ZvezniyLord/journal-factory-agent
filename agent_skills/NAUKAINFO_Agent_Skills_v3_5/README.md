# NAUKAINFO Agent Skills v3.5

Цей пакет переводить Journal Builder із моделі «скрипт викликає LLM» у модель «агент обирає скіли та викликає детерміновані інструменти».


## Єдиний вхідний скіл v3.5

Пакет експонує лише один активований Agent Skill: `skills/journal/SKILL.md`. Усі попередні `naukainfo-*` правила збережені як внутрішні `MODULE.md`; вони викликаються тільки головним скілом «журнал» і не повинні самостійно з’являтися в інших чатах.

## Основна архітектура

```text
Користувач
  ↓
LLM-агент / host (Codex, Claude Code, VS Code Agent, інший skills+MCP клієнт)
  ↓ progressive disclosure
Agent Skills (`skills/*/SKILL.md`)
  ↓ tool calls
NAUKAINFO MCP server (`mcp_server/server.py`)
  ↓ safe wrappers
Наявний `launcher.py` і модулі Journal Builder
  ↓
JSON reports / DOCX copy / PDF / quality gate
```

### Принцип

- **Priority 0:** `naukainfo-author-body-fidelity` захищає 100% тексту та ≥99% структури авторського тіла; усі інші скіли підпорядковані цьому gate.
- **Агент** планує, обирає скіли, аналізує неоднозначності й просить підтвердження.
- **Скіли** містять перевірені правила, послідовності, gotchas та критерії завершення.
- **MCP tools** виконують команди й повертають структуровані результати.
- **Існуючий код** залишається джерелом детермінованої логіки; новий шар не дублює `conference_pipeline.py`.
- Внутрішні LLM-виклики старого pipeline у новому agent-driven режимі мають бути вимкнені за замовчуванням. Неоднозначні рішення формує агент і зберігає як decision bundle.

## Вміст

- `AGENT.md` — базова роль головного агента.
- `skills/` — переносні Agent Skills у відкритому форматі `SKILL.md`.
  - evidence-based Excel↔DOCX matching by author + title;
  - structural insertion into the ETALON content slot before the protected tail section;
  - post-normalization re-evaluation of manual table-related page breaks using render comparison and the 60/40 balance rule;
  - table-format fidelity audit that resolves effective style inheritance and prevents ETALON `Normal` first-line indents from leaking into table cells;
  - canonical section/style application: English-only section headings plus structural ETALON styles for DOI/UDC, authors, titles, drawings, tables and references;
  - table/figure caption contract: right-aligned bold table number, centered bold table title, `TABLETEXT` cells, `РИС` object paragraph and `РисПід` caption;
  - reference-block fidelity: canonical `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` stamp, exact spacing, fresh per-article numbering and ETALON hanging indent;
  - semantic paragraph-role routing for DOI/UDC, author blocks, captions, lists and references;
  - editable SmartArt/shape/text-box fidelity checks and relationship repair.
  - multi-article assembly with semantic article-range extraction, per-article page breaks, two-pass TOC, and independent reference numbering restarted at 1.
  - annotation/keywords normalization with bold canonical labels and language-aware casing;
  - author-header cleanup that removes personal contacts without blank holes and normalizes metadata grammar;
  - manual/automatic reference-entry reconstruction, URL/DOI labels, and Ctrl+Space-equivalent cleanup;
  - missing-UDC online lookup request + operator-review gate and exact one-blank UDC spacing.
- `mcp_server/` — безпечний MCP-адаптер до наявного Journal Builder.
- `schemas/agent-decisions.schema.json` — контракт явних рішень агента.
- `docs/` — архітектура, контракт журналу, бізнес-правила, карта інтеграції та налаштування клієнтів.
- `tests/` — перевірка структури скілів і безпечних обмежень.

## Швидкий старт

1. Розпакуйте пакет у корінь проєкту або поруч із ним.
2. Встановіть залежності MCP-шару:

```powershell
python -m pip install -r mcp_server\requirements.txt
```

3. Встановіть змінну середовища:

```powershell
$env:NAUKAINFO_PROJECT_ROOT="X:\NAUKA_iNFO_Jornal\нова концепція"
```

4. Запустіть MCP server:

```powershell
python mcp_server\server.py
```

5. Додайте server до вашого MCP-сумісного агента за прикладом `docs/CLIENT_SETUP.md`.

## Режими ризику

- `read`: читання контексту, звітів, DOCX metadata.
- `scan`: сканування Excel/заявок, без Word COM і без зміни DOCX.
- `workspace-write`: створення копій і звітів лише в `_tmp`/workspace.
- `build`: повна збірка тільки після явного підтвердження `BUILD_CONFIRMED`.
- `finalize`: заборонено без зеленого quality gate і ручного підтвердження.

## Важливо

Поточний пакет є **agent layer + safe adapter**, а не заміною Journal Builder. Для повністю agent-driven неоднозначних рішень потрібен невеликий інтеграційний контракт `--agent-decisions`; він описаний у `docs/INTEGRATION_PLAN.md`.

## Команда «додай до скілів»

Коли користувач прямо каже «додай до скілів», агент зобов’язаний внести правило до реального пакета, оновити пов’язані документи/тести та changelog і повернути новий архів. Не можна обмежуватися усною обіцянкою або лише записом у пам’ять.

## v1.7 layout/style correction note

After applying canonical article styles, run the spacing/TOC gate: add required blank paragraphs after article titles, after figure/table/source blocks, before and after the reference stamp, and ensure only `SECTION`, `AUTOR`, and `Назва1` can feed the TOC. Clean reference runs equivalent to Word `Ctrl+Space` before applying `REFER` numbering.

## v1.8 multi-article assembly note

Build multiple articles only from validated semantic article ranges. After the final merge, recreate every reference list with a fresh numbering instance starting at 1, render to determine actual start pages, then materialize the static TOC and render again.


## v1.9 semantic normalization note

Use `Jurnal.dotx` as the authoritative style source. Normalize annotation/abstract and keywords labels, remove contacts from author headers without gaps, hard-stop on missing UDC pending online evidence and approval, reconstruct hand-numbered/Enter-split references, add URL/DOI labels, and rebuild every reference entry with Ctrl+Space-equivalent plain formatting before per-article numbering.

## v2.0 author-body fidelity note

The author body is immutable by default: 100% lexical identity, at least 99% structural identity, manual body lists stay manual, and every formatting/merge stage is followed by a fail-closed source-to-final audit. See `docs/SKILL_MAP.md`.


## v2.2 TOC/front-matter update
- TABLE OF CONTENTS is a real 3-column Word table, not loose paragraphs.
- TOC generation scans canonical styles only: `SECTION`, `AUTOR`, `Назва1`; output styles are `Tab_SEC`, `Tab_PIP`, `Tab_Taitl`.
- Article front matter is normalized to DOI/UDC -> author header -> one blank -> title -> one blank -> body.
- Split source titles are merged; duplicate title paragraphs created by the builder are prohibited.
- Page numbering from ETALON must be preserved by keeping the numbered middle section break before the final service page.

## v2.3 note
This release upgrades TOC rendering to the PDF-accurate table geometry. Use `scripts/rebuild_toc_pdf_contract.py` after page numbers are known.


## v2.5 full-release update
- Added `naukainfo-toc-author-cleaning` to prevent role/institution leakage into the Table of Contents.
- Upgraded TOC page detection: rendered page scan must ignore title occurrences inside the TOC itself.
- Verified on a 24-article conference 136 full release with 99 rendered pages.


Validation: 49 skills, 70 tests passed in v3.0.

## Project scope — critical

This skill package is project-scoped. Use it only for the project **«Дирежор»** / **NAUKAINFO Journal Builder**. Do not apply these skills, styles, business rules, section logic, TOC logic, or article-normalization rules in unrelated chats or other user projects unless the user explicitly asks to reuse them there.



## v2.6 scope and frontmatter update

- NAUKAINFO skills are project-scoped: only Дирежор / NAUKAINFO Journal Builder, only after activation in the current chat.
- Header cleanup now removes personal emails, damaged email fragments, phone/contact lines and author-written section notes without leaving blank paragraphs.
- Frontmatter normalization enforces DOI/UDC → cleaned header → title → annotation, while preserving the author body after annotation.


### v2.7
Adds numbering-definition fidelity for author body lists. This prevents bullet lists from becoming decimal lists during DOCX merge.


## v2.8 — Critical fidelity hotfixes

Historical v2.8 status: release was blocked until the new gates passed. Superseded by the verified v2.9/v30 release.

Added skills:
- `naukainfo-media-object-fidelity-gate` — blocks lost figures/drawings/media and caption detachment.
- `naukainfo-shape-textbox-nested-table-contract` — recursively inspects shapes/textboxes and nested tables/captions.
- `naukainfo-author-heading-emphasis-fidelity` — preserves author bold/italic/centered body subheadings.
- `naukainfo-frontmatter-supervisor-and-pip-split` — splits supervisors/people vs degrees/roles correctly.
- `naukainfo-table-caption-split-contract` — converts one-line table captions to canonical two-line format.
- `naukainfo-pagebreak-and-empty-paragraph-policy` — removes author page breaks and stray blanks while preserving required business blanks.
- `naukainfo-reference-language-and-marker-contract` — Ukrainian `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` vs English `REFERENCES`.

Regressions documented:
- Hnysiuk body list numbering changed due to numbering.xml collision.
- Magdysiuk Figure 2 was lost because media relationship fidelity was not deep enough.
- Magdysiuk body subheading bold was lost.
- Matviienko nested shape/table/caption content was not inspected recursively.
- Header classifier assigned `AUTOR` to degree/title lines in some cases.
- English reference blocks could receive the Ukrainian stamp.

Removed from active logic:
- text-only “content integrity” as a sufficient proof of journal safety;
- object-count-only checks without relationship/media/order validation;
- flat body scanning that ignores `w:txbxContent` and nested tables;
- generic replacement of all reference stamps with the Ukrainian heading.

## v2.9 — consolidated fidelity release

This release preserves all v2.8 backups and consolidates the critical rules into canonical `skills/<name>/SKILL.md` folders.

New gates:
- legacy binary DOC image recovery;
- atomic figure/object/caption cluster fidelity;
- multilingual marker library for captions/tables/references;
- unnumbered table-label recognition;
- final TOC/body author synchronization;
- immutable versioned backup policy.

Release evidence: conference 136, 24 articles, 99 rendered pages, 35 styled drawing paragraphs, 19 multilingual figure captions, 37 valid embedded-image relationships, five recovered Novak figures, and zero stale TOC author rows.


## v3.0 — verified fidelity and pagination release

Adds ETALON section/page-number fidelity, fake-leading-space cleanup, manifest-driven FREE LISTENERS TOC output, conservative unmarked-reference inference, exact annotation/keywords spacing, per-article media completeness, and clean `pageBreakBefore` article boundaries. Conference 136 verified output: 24 articles, 6 free listeners, 96 rendered pages.
