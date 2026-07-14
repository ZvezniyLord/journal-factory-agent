

---

# FILE: README.md

# NAUKAINFO Agent Skills v3.2

Цей пакет переводить Journal Builder із моделі «скрипт викликає LLM» у модель «агент обирає скіли та викликає детерміновані інструменти».


## Єдиний вхідний скіл v3.2

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


---

# FILE: AGENT.md

# Activation rule v3.2

Activate only the single project-scoped skill `journal`. All `naukainfo-*` MODULE.md files are internal and must not be activated independently. The skill is unavailable by default outside the Дирежор / NAUKAINFO Journal Builder project and the current explicitly activated chat.

# NAUKAINFO Journal Agent

Ти — головний агент зі складання наукових журналів NAUKAINFO. Ти не редагуєш DOCX «на око» і не переписуєш наявний pipeline. Ти плануєш роботу, активуєш потрібні Agent Skills, викликаєш детерміновані MCP tools і перевіряєш результат.

## Незмінні правила

0. **Найвищий пріоритет:** одразу активуй `naukainfo-author-body-fidelity`, створи source snapshot і захищай 100% лексики та щонайменше 99% структури тіла статті. Жодна верстка, стиль, нумерація чи LLM-рішення не може змінювати авторський текст. Ручні списки тіла не перетворюй на автоматичні; виняток — references.
1. Спочатку активуй `naukainfo-project-context` і прочитай project memory.
2. Перед новим кодом або новим алгоритмом знайди наявний модуль, функцію, тест чи перевірене рішення.
3. `ETALON-JOURNAL.docx` і raw conference folder — read-only. Працюй лише з копіями у workspace.
4. Не допускай прихованої втрати тексту, таблиць, рисунків, формул, shapes/textboxes, OLE, numbering або стилів.
5. У режимі мінімальної автентичності змінюй тільки явно дозволене: 11 pt, single spacing, таблиці без first-line indent, текст у shapes/textboxes 11 pt; інші ремонти — лише за окремим рішенням і з audit trail.
6. Кожна стаття починається з нової сторінки. Порядок статей і секцій визначає Excel/manifest і офіційна бібліотека секцій.
7. Вважай статтю знайденою лише після незалежної перевірки двох головних ознак: ПІБ автора та назви статті; у manifest завжди записуй точний файл і докази збігу.
8. У ETALON вставляй контент структурно після сторінки TABLE OF CONTENTS і перед paragraph-level section break, що починає захищену хвостову сторінку; не використовуй фіксований номер абзацу.
9. LLM-рішення не можуть перебивати text/object integrity audit або quality gate.
10. УДК, автоматично запропонований агентом, завжди позначається `needs_operator_review`.
11. Не запускай повну збірку, доки не виконано preflight; для діагностичного build дозволь запуск із проблемами тільки за явним запитом користувача.
12. Після кожного запуску активуй `naukainfo-project-memory` і зафіксуй, що спрацювало, що не спрацювало, артефакти та регресії.
13. Фраза користувача «додай до скілів» є прямою обов’язковою командою: реально онови пакет Agent Skills, відповідні правила/тести й changelog та видай новий архів; простого підтвердження в чаті недостатньо.
14. Після нормалізації 14→11 pt не зберігай авторські ручні page breaks механічно: активуй `naukainfo-pagination-break-reflow` для кандидатів біля таблиць, але ніколи не видаляй structural/article-start breaks.
15. Після вставки в ETALON активуй `naukainfo-table-format-fidelity`: перевіряй ефективне форматування таблиць через style inheritance, а не лише direct properties; якщо в оригіналі немає абзацного відступу, у копії встанови прямий нульовий override, не змінюючи глобальний стиль `Normal`.

16. Автоматично оновлюй скіли, бізнес-правила, контракт, інтеграційний план, архітектуру, README, changelog і тести після кожного підтвердженого стабільного виправлення; не чекай повторного нагадування користувача. Неперевірені припущення не фіксуй як правила.
17. Перед фінальним build активуй `naukainfo-semantic-style-routing`: анотація/abstract і ключові слова використовують звичайний `Normal` з абзацним відступом; службові метадані, авторські блоки, назви, рисунки, підписи, таблиці, списки та references не можуть успадковувати позитивний first-line indent від `Normal`; hanging indent references дозволений.
18. Якщо стаття містить SmartArt, shapes або textboxes, активуй `naukainfo-shape-object-fidelity` і перевір OOXML relationships, текст, extent та render; не перетворюй редаговані фігури на растр без дозволу.

19. Після вставки кожної статті активуй `naukainfo-canonical-style-application`: назву секції бери лише з офіційної бібліотеки, вставляй англійською один раз перед першим матеріалом секції та структурно застосовуй `SECTION`, `UDC`, `AUTOR`, `pip`, `Назва1`, `РИС`, `РисПід`, `TABLETEXT`, `REF-TITLE`, `REFER`. Візуальна схожість без реальних style IDs є помилкою.

## Типовий цикл

1. Context → 2. Preflight/scan → 3. Resolve ambiguities → 4. Plan → 5. Human approval → 6. Build on copies → 7. DOCX audits → 8. Visual audit → 9. Quality gate → 10. Memory update.

## Рішення агента

Не залишай важливі рішення лише в чаті. Записуй їх у `agent_decisions.json` за схемою `schemas/agent-decisions.schema.json`. До інтеграції `--agent-decisions` цей файл є audit trail; після інтеграції він стає явним input pipeline.

20. Після canonical style application активуй `naukainfo-table-figure-caption-contract`: номер таблиці праворуч і напівжирний, назва по центру і напівжирна, table cells=`TABLETEXT`, drawing paragraph=`РИС`, caption=`РисПід`; усі ці ролі без позитивного first-line indent і з повним render-аудитом.
21. Перед pagination/TOC активуй `naukainfo-reference-block-fidelity`: україномовний штамп рівно `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`, один порожній абзац до нього і один після, `REF-TITLE`/`REFER`, свіжа нумерація від 1 і еталонний висячий відступ без copied direct indents/tabs.


## v1.7 layout/style correction note

After applying canonical article styles, run the spacing/TOC gate: add required blank paragraphs after article titles, after figure/table/source blocks, before and after the reference stamp, and ensure only `SECTION`, `AUTOR`, and `Назва1` can feed the TOC. Clean reference runs equivalent to Word `Ctrl+Space` before applying `REFER` numbering.

22. Для журналу з двома або більше статтями активуй `naukainfo-multi-article-assembly`: перенось лише семантичні article ranges, після merge створи distinct numbering instance від 1 для кожного reference block, стабілізуй пагінацію до TOC, видали appended section artifacts і перевір точні source↔final text/table/object signatures.

23. Перед фінальним render активуй `naukainfo-annotation-keywords-normalization`: `Анотація.`/`Abstract.` і `Ключові слова:`/`Keywords:` — напівжирна лише мітка; обидва абзаци `Normal`, не heading.
24. Активуй `naukainfo-author-header-cleanup`: видали email/телефон/messenger без порожніх рядків, збережи ORCID, нормалізуй регістр ролей і перевір `AUTOR`/`pip`.
25. Якщо UDC немає — зупини build, створи online lookup packet через `naukainfo-udc-review`, дочекайся approval; після UDC рівно один blank.
26. Перед `REFER` активуй `naukainfo-reference-entry-reconstruction`: віднови межі ручної нумерації/Enter-продовжень, очисти записи як Ctrl+Space, додай `URL:`/`DOI:` і перезапусти список з 1 у кожній статті.
27. Канонічні стилі завжди копіюй із поточного `Jurnal.dotx`; не відтворюй `SECTION` або `pip` ручними властивостями.

28. Після кожного підтвердженого оновлення підтримуй `docs/SKILL_MAP.md` і коротко фіксуй у changelog: що спрацювало, що не спрацювало та що вилучено з активної логіки. Невдалі підходи не дублюй у діючих правилах.


## v2.2 TOC/front-matter update
- TABLE OF CONTENTS is a real 3-column Word table, not loose paragraphs.
- TOC generation scans canonical styles only: `SECTION`, `AUTOR`, `Назва1`; output styles are `Tab_SEC`, `Tab_PIP`, `Tab_Taitl`.
- Article front matter is normalized to DOI/UDC -> author header -> one blank -> title -> one blank -> body.
- Split source titles are merged; duplicate title paragraphs created by the builder are prohibited.
- Page numbering from ETALON must be preserved by keeping the numbered middle section break before the final service page.


## v2.5 full-release TOC author/page rule

For full journal releases, the TOC is generated only after rendering and page detection that excludes TOC-title occurrences. TOC author cells use a cleaned author map and may contain only participant names. Roles, institutions, degrees, ORCID, locations and contacts must not leak into TOC author cells.

## Project scope — critical

This skill package is project-scoped. Use it only for the project **«Дирежор»** / **NAUKAINFO Journal Builder**. Do not apply these skills, styles, business rules, section logic, TOC logic, or article-normalization rules in unrelated chats or other user projects unless the user explicitly asks to reuse them there.



## v2.6 scope and frontmatter update

- NAUKAINFO skills are project-scoped: only Дирежор / NAUKAINFO Journal Builder, only after activation in the current chat.
- Header cleanup now removes personal emails, damaged email fragments, phone/contact lines and author-written section notes without leaving blank paragraphs.
- Frontmatter normalization enforces DOI/UDC → cleaned header → title → annotation, while preserving the author body after annotation.


## v2.7 numbering guard
Never treat a preserved paragraph `numPr` as safe until the referenced `numbering.xml` definition is verified. If source body bullet renders as decimal in final, stop and repair numbering definitions without changing text.


## v2.8 — Critical fidelity hotfixes

Status: full release v2.6/v2.8 is not considered publishable until the new gates pass on all 24 source articles.

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

## v2.9 mandatory release sequence

1. Preserve versioned backups; never overwrite source, prior release, or prior skills ZIP.
2. Run author-body and numbering-definition fidelity before transformations.
3. For legacy `.doc`, compare source rendering to converted DOCX and recover omitted OLE images when needed.
4. Treat figure/object/caption/source as an atomic cluster and recurse into shapes/textboxes/nested tables.
5. Normalize multilingual table/figure/reference markers conservatively.
6. Complete final AUTOR/pip classification, then rebuild TOC from the final body—not from an older TOC.
7. Render every page, update page numbers, rerender, and run media/hash/TOC-sync audits.
8. A text-only or object-count-only report is never sufficient proof of fidelity.

## v3.0 mandatory release behavior

Before claiming a journal release is final, preserve the ETALON three-section/page-number signature, compare every source article’s text/run/object signatures, use `pageBreakBefore` for all article starts, infer only strongly evidenced terminal references, add the manifest-driven FREE LISTENERS TOC section, render all pages twice around TOC page updates, and fail closed on any missing object or emphasis loss.


---

# FILE: CHANGELOG.md

# v3.2.0

- Added fail-closed required-assets startup gate.
- A missing ETALON/Jurnal.dotx/manifest/master skill now blocks the build.
- Added exact ETALON section, page numbering, footer, and style-ID validation.
- Added `scripts/preflight_required_assets.py`.
- Added `docs/STARTUP_ASSET_CONTRACT.md`.
- Prohibited creating replacement journals from blank DOCX when templates are unavailable.

# v3.2 — single master skill `journal`

Validation: 74 tests passed; 1 discoverable skill validated.

- Replaced 49 independently discoverable skills with one discoverable skill: `skills/journal/SKILL.md`.
- Preserved all previous skill content as internal `MODULE.md` files and retained v3.0 as backup.
- Added universal per-article deep text-integrity audit script.
- Added fail-closed rule: no author-name/article-title branches in production logic.
- Added native-source audit finding: 0 confirmed unapproved text changes across 24 articles; 1 legacy object-order case remains REVIEW.
- Added explicit distinction between lexical PASS and full text/object/run-format certification.


## v2.5 — Project scope guard

- Added `docs/PROJECT_SCOPE.md`.
- Added `naukainfo-project-scope-guard` to the skill map.
- Clarified that NAUKAINFO Agent Skills are limited to project «Дирежор» / NAUKAINFO Journal Builder.
- Removed the unsafe implicit assumption that these business rules may be applied in unrelated chats or projects.



## v2.5 - 24-article full release QA

### Added
- `naukainfo-toc-author-cleaning` for clean participant-only author cells in the static TOC.
- Full-release TOC page-detection guard: ignore title matches inside TOC pages; scan rendered body pages only.

### Worked
- PDF-accurate 3-column TOC table from v2.3.
- Two-pass render → page detection → TOC update → re-render.
- Manual clean author map for ambiguous headers with roles/institutions on adjacent lines.

### Did not work / removed from active logic
- Using the first title occurrence in the rendered PDF as the article page number. This selects TOC pages.
- Joining all `AUTOR` paragraphs for TOC author cells. This leaks roles, degrees, institutions and city lines when a source header is irregular.
# Changelog

## v2.0 — Priority-0 author-body fidelity

### Added
- `naukainfo-author-body-fidelity` as the highest-priority skill.
- `audit_author_body_fidelity.py` and a 100% lexical / 99% structural fail-closed gate.
- `docs/SKILL_MAP.md` with execution order and pruning policy.

### Worked
- Source/final semantic signatures; allowed-change whitelist; manual-list preservation; repeated integrity checks.

### Did not work / removed from active logic
- Visual-similarity-only acceptance.
- Plain-text reconstruction of article bodies.
- Automatic conversion of all body lists.
- Unrequested grammar/style rewriting of scientific text.

## 1.9.0

- Added `naukainfo-annotation-keywords-normalization`: canonical bold labels, punctuation, language-aware casing, and authoritative Normal paragraph geometry.
- Added `naukainfo-author-header-cleanup`: email/phone/messenger removal without blank holes, ORCID preservation, role capitalization and `AUTOR`/`pip` verification.
- Added `naukainfo-reference-entry-reconstruction`: hand-typed numbering and Enter-split continuation repair, URL/DOI labels, ambiguity stop condition, and Ctrl+Space-equivalent rebuild.
- Upgraded `naukainfo-udc-review` with an online evidence packet, operator approval gate, insertion helper and exactly one blank after UDC.
- Made `Jurnal.dotx` the sole authoritative source of canonical style nodes; removed the failed visual-approximation `apply_canonical_article_styles.py` path and the incorrect zero-indent rule for annotation/keywords.
- Added two contact-bearing project-derived DOCX fixtures and new regression tests.
- Rebuilt and visually verified the two-article conference 136 journal; both reference lists independently restart at 1.

## 1.8.0

- Added `naukainfo-multi-article-assembly` for semantic extraction and composition of multiple validated articles into one ETALON journal.
- Added a hard per-article reference-numbering gate: every article receives a distinct `numId` with `startOverride=1`; continuation from a previous article is a build failure.
- Added the two-pass TOC workflow: stabilize pagination first, then insert actual internal start pages and re-render.
- Added trailing-section cleanup to prevent blank pages caused by appended article `sectPr` artifacts.
- Added exact article text/table sequence comparison and media/SmartArt preservation checks after merge.
- Added `scripts/multi_article_reference_restart.py`, dependency `docxcompose>=1.4`, and a regression test for two independent reference blocks.
- Verified a two-article draft journal: 19 physical pages, 3 tables, 5 article visuals, references 4+24, both lists starting at 1, no text loss and no final blank page.

## 1.7.0

- Added `naukainfo-spacing-toc-contract` for required blank paragraphs after article titles, figure/table/source blocks, and before/after the canonical reference stamp.
- Corrected reference-block contract: after `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` there must be one empty paragraph before the first source.
- Added TOC/outline gate: only `SECTION`, `AUTOR`, and `Назва1` may have outline levels; `pip` and all service/body styles must be excluded from generated TOC logic.
- Added Ctrl+Space-equivalent cleanup of reference runs to remove copied character overrides, hyperlink styles, underline/color, shadows and foreign substyles before applying `REFER`.
- Replaced failed acceptance logic: visual similarity without structural styleId/outline audit is no longer sufficient.
- Added deterministic `scripts/enforce_spacing_toc_references.py` and spacing/TOC regression tests.

## 1.6.0

- Added `naukainfo-table-figure-caption-contract` with verified table-number/title, `TABLETEXT`, `РИС`, `РисПід` and source-note rules.
- Added `naukainfo-reference-block-fidelity` with the canonical `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` stamp, exact blank spacing and per-article numbering restart.
- Fixed the regression where `REFER` paragraphs retained copied direct indentation/tabs and foreign `numId`, causing bullets/arrows and incorrect hanging alignment.
- Added deterministic `scripts/normalize_captions_references.py` plus caption/reference regression tests.
- Reprocessed the Hnysiuk article (1 table, 1 editable SmartArt, 4 references) and the Soloviov–Halenko–Debretseni article (2 tables, 4 figures, 24 references), with full render QA.
- Updated business rules, journal contract, integration plan, architecture, agent instructions and README.

## 1.5.0

- Added `naukainfo-canonical-style-application`.
- Made English-only section headings mandatory, resolved from the official section library and inserted once before the first article of each non-empty section.
- Made actual ETALON style IDs mandatory for section, DOI/UDC, author names, author metadata, title, drawing paragraphs, figure captions, table cells, reference heading and reference entries.
- Added deterministic `scripts/apply_canonical_article_styles.py` and regression test.
- Verified conference 136 Hnysiuk article as section 1: `ECONOMIC THEORY, MACRO- AND REGIONAL ECONOMY`.
- Corrected the Hnysiuk ETALON copy and removed the obsolete table page break after rendered A/B review.

## 1.4.0

- Added `naukainfo-semantic-style-routing` with a canonical paragraph-role/style map.
- Added a hard no-positive-first-line-indent rule for DOI/UDC, author metadata, titles, annotations, keywords, drawing paragraphs, figure/table captions, source notes, table cells, list items, reference headings and reference entries.
- Preserved intentional hanging indents and numbering geometry in references/lists.
- Added deterministic `scripts/semantic_paragraph_roles.py` and regression tests.
- Added `naukainfo-shape-object-fidelity` for SmartArt, grouped shapes, text boxes, DrawingML/VML and diagram relationship parts.
- Added deterministic shape normalization/audit scripts and a textbox regression test.
- Verified SmartArt transfer on the Hnysiuk motivation article and semantic-indent repair on both Hnysiuk and Soloviov–Halenko–Debretseni ETALON copies.
- Made verified skill/business-rule/documentation/test updates an automatic project obligation, without requiring the user to repeat the reminder.


## 1.3.0

- Added `naukainfo-table-format-fidelity` to prevent template style inheritance from changing table text placement.
- Added effective first-line indent resolution through direct paragraph properties, paragraph style, base-style chain, and defaults.
- Added deterministic `scripts/table_format_fidelity.py` and regression tests.
- Added the rule to use a direct zero override in table cells instead of changing the global ETALON `Normal` style.
- Expanded the journal contract, integration/business plan, architecture, ready-solutions register, and business-rules documentation.
- Verified the rule on the Soloviov–Halenko–Debretseni article: 49 inherited table indents corrected, zero remaining table paragraph/run differences after save/re-open.

## 1.2.0

- Added `naukainfo-pagination-break-reflow` for rendered A/B evaluation of author-inserted manual page breaks after 14→11 pt normalization.
- Added the publication-layout rule: remove an obsolete table-related break only when the table fits whole or splits no rougher than approximately 60/40 by rendered table volume.
- Added safeguards for captions, header rows, merged cells, notes, structural breaks, article-start breaks, and ambiguous cases.
- Added a hard agent-governance rule: “додай до скілів” requires an actual package update, tests/docs/changelog updates, and a new archive.
- Updated `naukainfo-minimal-normalization` and the journal contract to invoke the new pagination reflow review.

## 1.1.0

- Added `naukainfo-manifest-evidence-matching`: exact Excel↔DOCX audit using author name and article title as independent primary signals.
- Added `naukainfo-etalon-slot-insertion`: structural insertion after TABLE OF CONTENTS and before the protected tail section.
- Added deterministic `scripts/insert_article_into_etalon.py`.
- Documented verified object-preserving template insertion and required render audit.

## 1.0.0

- Added 11 portable NAUKAINFO Agent Skills.
- Added safe MCP adapter around the current Journal Builder CLI.
- Added explicit Agent Decision Bundle schema.
- Added read-only scan, inspection, test and rendering tools.
- Added build approval and path-isolation safeguards.
- Added integration plan for removing nested LLM decisions from the pipeline.

## v2.1
- Added `naukainfo-skill-map-change-log`.
- Updated author body fidelity: body lists remain author-original; only references are canonicalized.
- Updated multi-article assembly: static TOC is inserted first, rendered, page numbers corrected, then re-rendered.
- Documented the successful 6-article assembly pass and the discarded unsafe approach: changing body lists as if they were references.


## v2.2
- Added `naukainfo-toc-table-builder`: TOC must be a three-column Word table using `Tab_SEC`, `Tab_PIP`, `Tab_Taitl`, generated from `SECTION`/`AUTOR`/`Назва1` styles and final pagination.
- Added `naukainfo-front-matter-order-and-title-dedupe`: canonical DOI/UDC -> author header -> title order; exactly one blank before and after title; duplicate generated titles are forbidden.
- Fixed regression notes: loose paragraph TOC and manual `body_start_idx` title duplication are removed from active logic.
- Fixed page numbering preservation rule: the middle numbered section break from ETALON must be preserved before the final service page.

## v2.3 - PDF-accurate TOC geometry
- Upgraded `naukainfo-toc-table-builder` after PDF visual comparison.
- Fixed the v2.2 defect where article author/title/page were placed in one row and three equal columns.
- Added `scripts/rebuild_toc_pdf_contract.py`.
- New contract: merged section rows; per article two rows; number/content/page columns with fixed grid `[600, 8300, 739]` twips.
- Removed active logic that repeats section text in all three cells.


## v2.6 — scope guard + frontmatter/contact cleanup regression

- Strengthened project-scope boundary: these skills are only for the Дирежор / NAUKAINFO Journal Builder project and only after activation in the current chat.
- Fixed full-release regressions: author emails, damaged email remnants, author-supplied section notes, and comma-joined author/degree lines.
- Added anti-regression rule for canonical frontmatter order: DOI/UDC → header → title → annotation/abstract.
- Reconfirmed: author body after annotation must remain untouched except explicitly allowed NAUKAINFO normalization.


## v2.7
- Added `naukainfo-numbering-definition-fidelity`.
- Fixed regression where Hnysiuk body bullet list became decimal `1.`/`2.` after merge due to numbering.xml `numId` collision.
- Added rule: author body list markers are protected author structure; only references may be rebuilt as decimal restart lists.


## v2.8 — Critical fidelity hotfixes

Status: full release v2.6/v2.8 is not considered publishable until the new gates pass on all 24 source articles.

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

## v2.9

- Preserved v2.8 and all earlier versioned backups; created a new clean package instead of overwriting.
- Migrated seven loose v2.8 skill files into canonical `skills/<name>/SKILL.md` directories.
- Added legacy binary DOC image recovery after the Novak regression exposed converter-omitted figures 1 and 4.
- Added atomic figure-cluster fidelity and SHA-256/relationship auditing.
- Added multilingual marker library, including German `Abb.`, `Literaturverzeichnis`, and `Quellenverzeichnis`.
- Added unnumbered table-label recognition after the Slabky article used standalone `Таблиця`.
- Added final TOC/body author synchronization after stale TOC content omitted Papinko and leaked `Hon. PhD`.
- Normalized English `REFERENCES`, numbered Ukrainian reference headings, and restored author bold emphasis for `13. Висновки`.
- Verified the repaired 24-article release on 99 rendered pages.

## 3.0.0 — 2026-07-11

### Added
- `naukainfo-etalon-section-pagination-fidelity`.
- `naukainfo-body-leading-space-normalization`.
- `naukainfo-free-listener-toc-section`.
- Verified v32 deterministic finalizer and release report.

### Changed
- Exact annotation→keywords→blank spacing.
- Article boundaries use `pageBreakBefore`, not dummy break paragraphs.
- Per-article media gate includes Todorova/Magdysiuk regression fixtures.
- Nested shape/textbox/table caption styling is recursively asserted.
- Reference block can be inferred at article end only with strong evidence.
- TOC includes the final manifest-driven `FREE LISTENERS` section.

### Worked
- Three ETALON sections and page-number footer survived assembly.
- 24 article starts, 6 listener records, and 96 rendered pages verified.

### Removed from active logic
- Aggregate object counts as sufficient fidelity proof.
- Break-only paragraphs between articles.
- Global whitespace cleanup.
- Marker-only bibliography detection.


---

# FILE: docs/PROJECT_SCOPE.md

# Project Scope / Межі застосування скілів

## Статус
Цей пакет скілів є **проєктним**, а не універсальним.

## Дозволена область застосування
Скіли пакета `NAUKAINFO_Agent_Skills` застосовуються **лише** в межах проєкту **«Дирежор»** та його підпроєкту **NAUKAINFO Journal Builder**:

- збірка журналів NAUKAINFO;
- обробка статей, заявок, Excel/manifest, ETALON/Jurnal.dotx;
- підготовка змісту, стилів, УДК, DOI, URL, references, авторських шапок;
- перевірка відповідності бізнес-плану саме NAUKAINFO.

## Заборонено
Не використовувати ці правила як загальні правила для інших чатів, клієнтів, документів або не пов’язаних із «Дирежором» задач.

Заборонено переносити в інші проєкти такі правила без прямого дозволу користувача:

- стилі `SECTION`, `UDC`, `AUTOR`, `pip`, `Назва1`, `TABLETEXT`, `REFER`, `REF-TITLE`, `Tab_SEC`, `Tab_PIP`, `Tab_Taitl`;
- правила NAUKAINFO щодо змісту, секцій, УДК, DOI/URL, references;
- логіку збереження авторського тіла статті саме під журнал NAUKAINFO;
- карту скілів і бізнес-правила цього пакета.

## Пріоритет
Якщо запит не належить до проєкту «Дирежор» / NAUKAINFO Journal Builder, цей пакет не активується. Для інших чатів потрібно використовувати лише загальні інструкції середовища або окремо надані користувачем правила.


## Активація за умовчанням заборонена

Ці скіли не є глобальною пам’яттю і не мають застосовуватися автоматично в інших чатах.
Вони активуються тільки коли одночасно виконані умови:

1. чат/проєкт явно належить до **«Дирежор» / NAUKAINFO Journal Builder**;
2. користувач прямо просить працювати з цими скілами або задача очевидно є збіркою/аудитом журналу NAUKAINFO;
3. немає конфліктних інструкцій поточного чату.

У звичайних чатах, інших проєктах або документах за замовчуванням потрібно діяти за дефолтними інструкціями середовища та інструкціями конкретного чату. Заборонено переписувати або переносити ці скіли до іншого контексту без окремої прямої команди користувача.

## Конфлікт інструкцій

Якщо інший чат має власні правила документа, шаблону, стилів або верстки, вони мають пріоритет у тому чаті. Правила NAUKAINFO не можна підмішувати, навіть якщо задача також пов’язана з DOCX/Excel/PDF.

## v3.0 activation reminder
This package remains visible and active only inside the Дирежор / NAUKAINFO Journal Builder project and this explicitly activated workflow. Other chats use their own local instructions and default document behavior.


## v3.1 activation boundary

Only `skills/journal/SKILL.md` is discoverable. Internal `MODULE.md` files must never be loaded as standalone skills. Activation is explicit and limited to the current Дирежор chat.


---

# FILE: docs/STARTUP_ASSET_CONTRACT.md

# Startup Asset Contract

## Purpose

This contract prevents a chat, agent, or application from inventing a journal when the production template is missing.

## Required folder layout

```text
JOURNAL_FACTORY_MASTER_v1/
  00_START_HERE/
  01_SKILL_JOURNAL/
  02_TEMPLATES_REQUIRED/
  03_REFERENCE_RELEASES/
  04_TECHNICAL_SPEC_FOR_APP/
  05_TESTS_QA_AND_SCHEMAS/
  06_SAMPLE_INPUT_ARCHIVE/
  07_OUTPUT_CONTRACT_AND_EXAMPLES/
  08_ARCHIVE_NOT_FOR_PRODUCTION/
```

## Blocking rule

No ETALON = no build. No Jurnal.dotx = no build. No manifest = no build. No master skill = no build.

Never create a replacement cover, TOC, style set, sections, footers, or page numbering from a blank document. Work only in a copy of `ETALON-JOURNAL.docx`.

## Reference release rule

`JOURNAL_136_FINAL_RELEASE_v33.docx` is used only for regression comparison. It is never a content source.

## Required result

A build may be released only after the per-article lexical/run/table/object audits, ETALON signature audit, final pagination/TOC rebuild, and full-page render inspection have passed.


---

# FILE: docs/BUSINESS_RULES.md

# Бізнес-правила NAUKAINFO Journal Builder

## ПРАВИЛО №1 — абсолютна цілісність авторського тіла статті

Це правило має вищий пріоритет за косметичну верстку, компактність сторінок і будь-які автоматичні «покращення». Текст тіла статті не переписується, не скорочується, не доповнюється, не переставляється і не виправляється стилістично без прямого рішення оператора.

- Ціль: **100% лексичної тотожності** тіла статті після виключення чітко дозволених службових нормалізацій.
- Мінімум: **99% структурної тотожності** абзаців, списків, таблиць, рисунків, формул, підписів, приміток та порядку об’єктів.
- Ручні списки в тілі залишаються ручними; автоматичні залишаються автоматичними. Конвертація за замовчуванням заборонена. Виняток — бібліографічний блок `REFER`.
- Дозволено лише: 11 pt/single, канонічні стилі до маркерів, очищення/граматика шапки, UDC/DOI/URL/annotation/keywords/reference normalization, технічні відступи та page-break repairs без зміни змісту.
- Кожна операція має завершуватися source→final content-integrity audit. Неузгоджена різниця є build failure.

## Принцип автентичності таблиць

Таблиця у фінальному журналі повинна відтворювати авторське розміщення тексту, крім явно дозволених змін 11 pt і single spacing. Вставлення в `ETALON-JOURNAL.docx` не може непомітно додавати абзацні відступи через стилі шаблону.

### Обов’язкова бізнес-перевірка

- Основні докази відповідності таблиці: точний текст клітинок і збіг структури таблиці.
- Для кожного table paragraph перевіряється effective formatting, а не лише direct XML.
- Якщо в оригіналі first-line indent відсутній/нульовий, фінальна копія також має 0.
- Виправлення виконується локальним override у клітинці; глобальні стилі ETALON не змінюються.
- Перевіряються вирівнювання, інтервали, run formatting, vertical alignment, widths, merges, row split і captions.
- Після виправлення документ повторно відкривається, порівнюється і рендериться.

### Критерій приймання

`PASS` можливий лише коли:

1. кількість і структура таблиць збережені;
2. текст клітинок і порядок runs збережені;
3. effective first-line indent відповідає оригіналу;
4. немає нез’ясованих formatting differences;
5. усі сторінки документа, особливо сторінки з таблицями, пройшли visual QA.

### Заборонено

- змінювати `Normal` у master shell заради однієї статті;
- вважати `first_line_indent=None` доказом відсутності відступу;
- реконструювати таблицю без потреби;
- приймати документ лише за object counts без візуального рендеру.


## Семантичні ролі та абзацні відступи

`Normal` у `Jurnal.dotx` має first-line indent 1 см. Його використовують звичайний основний текст, абзац анотації/abstract і абзац ключових слів; для анотації та ключових слів зберігається звичайний абзацний відступ. DOI, УДК/UDC, авторські дані, назва статті, рисунки/SmartArt, підписи та джерела до рисунків, номер/назва/джерело таблиці, текст усередині таблиць, марковані/нумеровані пункти, заголовок references і reference entries не можуть отримувати позитивний first-line indent. У reference entries дозволений hanging indent, який вирівнює номер і продовження запису.

Канонічна карта стилів ETALON: `SECTION`, `UDC`, `AUTOR`, `pip`, `Назва1`, `РИС`, `РисПід`, `TABLETEXT`, `REF-TITLE`, `REFER`. Призначення стилю не може змінювати зміст, numbering, TOC/outline або авторське вирівнювання без окремої перевірки. Якщо стиль дає небажаний side effect, застосовується вузький direct override firstLine=0.

## Редаговані фігури

SmartArt, grouped shapes і textboxes є структурними OOXML-об’єктами. Їх текст, data/drawing relationships, extents, anchors і fallback content зберігаються. Растеризація без явного дозволу заборонена.


## Canonical section and style application (v1.5)

- Section headings in the journal body are English-only, resolved by `section_id` from the official project section library, inserted once before the first article of a non-empty section, and styled `SECTION`.
- For the Hnysiuk article in conference 136, section 1 is verified as `ECONOMIC THEORY, MACRO- AND REGIONAL ECONOMY`.
- The final DOCX must contain actual style IDs: DOI/UDC=`UDC`, human names=`AUTOR`, author metadata=`pip`, title=`Назва1`, drawing paragraph=`РИС`, figure caption=`РисПід`, table cells=`TABLETEXT`, reference heading=`REF-TITLE`, reference entries=`REFER`.
- A visually similar result with `Normal` style is a build failure. Style assignment is followed by reopen audit and full render.

## Таблиці, рисунки та підписи — канонічний контракт v1.6

### Таблиця

- Номер таблиці є окремим абзацом над назвою: `Таблиця N` / `Table N`.
- Номер: праворуч, напівжирний, 11 pt, single, first-line indent 0, 0 pt до/після, `keep_with_next`.
- Назва таблиці: наступний непорожній абзац, по центру, напівжирний, 11 pt, single, first-line indent 0, 0 pt до/після, не відривати від таблиці.
- Усі абзаци в клітинках мають фактичний стиль `TABLETEXT`; авторське вирівнювання та виділення зберігаються.
- Примітка/джерело під таблицею: 11 pt, single, first-line indent 0; курсив і вирівнювання зберігаються з оригіналу.

### Рисунок / SmartArt / shapes

- Абзац із об’єктом має фактичний стиль `РИС`, по центру, без абзацного відступу.
- Підпис розташовується під об’єктом, має фактичний стиль `РисПід`, по центру, 11 pt, single, first-line indent 0.
- Нормальна форма підпису: `Рис. N. Назва`; для англомовної статті допускається `Figure N. ...`.
- Джерело під рисунком не має позитивного first-line indent; авторське виділення зберігається.
- Редаговані DrawingML/SmartArt об’єкти не растеризуються.

## Блок використаних джерел — канонічний контракт v1.6

- Для україномовних статей штамп є рівно `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`.
- Варіанти `СПИСОК ВИКОРИСТАНОЇ ЛІТЕРАТУРИ`, `ЛІТЕРАТУРА` та інші авторські назви нормалізуються до штампа.
- Перед штампом має бути рівно один порожній абзац; після штампа перед записом 1 також має бути рівно один порожній абзац.
- Штамп має фактичний стиль `REF-TITLE`, по центру, 11 pt, single, first-line indent 0, `keep_with_next`.
- Кожний запис має фактичний стиль `REFER`, 11 pt, single, 0 pt до/після, вирівнювання по ширині.
- Для кожної статті створюється окремий numbering instance з початком від 1; чужий `numId` із raw DOCX не переноситься.
- Прямі `w:ind` і tab stops, що перебивають ETALON, видаляються. Геометрію дає еталонне numbering: left/hanging 567 twips (приблизно 1 см).
- Продовження запису вирівнюється по лінії тексту, а не під номером; маркери, стрілки або tab-artifacts є build failure.


## Проміжки, таблиці/рисунки та TOC — уточнення v1.7

### Порожні абзаци

- Після назви статті (`Назва1`) обов’язково має бути один порожній абзац перед анотацією або основним текстом.
- Після кожної таблиці має бути один порожній абзац. Якщо під таблицею є рядок `Джерело: ...`, цей рядок вважається частиною таблиці, тому порожній абзац ставиться після `Джерело`, а не між таблицею і джерелом.
- Після рисунка/SmartArt має бути один порожній абзац після підпису або після рядка `Джерело`, якщо він є.
- Перед штампом `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` має бути один порожній абзац.
- Після штампа `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` також має бути один порожній абзац перед першим бібліографічним записом.

### Список джерел

- Увесь блок джерел очищується від перенесених character overrides так, як після `Ctrl+Space`: прибираються підстилі, ручні підкреслення, тіні, кольори, чужі hyperlink/run styles і сторонні прямі властивості, якщо вони не є частиною еталонного `REFER`.
- Геометрія списку задається не ручними пробілами і не tab-artifacts, а стилем `REFER` плюс новий numbering instance від 1 для кожної статті.
- Штамп завжди `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`; авторські варіанти `СПИСОК ВИКОРИСТАНОЇ ЛІТЕРАТУРИ` не допускаються.

### TOC / heading levels

- У зміст мають потрапляти лише: назва секції (`SECTION`), ПІБ автора (`AUTOR`) і назва статті (`Назва1`).
- `pip` не є заголовком і не може мати outline level або heading inheritance.
- Якщо стиль у Word зовні схожий на еталон, але має неправильний outline level, це build failure.

### Що спрацювало / що не спрацювало

- Спрацювало: перевірка реального OOXML styleId, окремий numbering instance для кожного reference block, пряме очищення run-level overrides у джерелах, rendered QA сторінок із таблицями/рисунками.
- Не спрацювало й вилучається з логіки прийняття: візуально-подібне форматування без перевірки styleId/outline; просте присвоєння `REFER` без очищення чужих `numId`, tabs і run overrides; припущення, що `pip` безпечно наслідує стиль шаблону без structural audit.


## Багатостатейна збірка — контракт v1.8

- До master shell переносяться лише семантичні діапазони статей: від `SECTION` до останнього `REFER`, без повторних обкладинок, службових сторінок і хвостової сторінки.
- Кожна стаття починається з нової сторінки. Назва секції вставляється один раз перед першим матеріалом секції; при переході до іншої секції додається новий англомовний `SECTION`.
- Після остаточного злиття кожний блок джерел отримує окремий numbering instance, distinct `numId` і `startOverride=1`. Нумерація другої або наступної статті не може продовжувати попередню.
- TOC формується у два проходи: спочатку стабілізується пагінація, потім вносяться фактичні внутрішні сторінки початку статей і виконується повторний render.
- Після merge обов’язково порівнюються точні послідовності текстових абзаців і таблиць кожної статті з валідованим source, а також media/diagram signatures.
- Порожня сторінка після хвостової службової сторінки є build failure; appended `sectPr` артефакти видаляються.

### Перевірене рішення

Спрацювало: trim семантичного article range → `docxcompose` для relationship/media import → targeted cleanup section artifacts → fresh reference numbering → render → static TOC → final render.

Не спрацювало й не використовується: append повних одно-статейних журналів; довіра до source `numId` після merge; TOC до стабілізації пагінації; acceptance лише за object counts.


## Семантика анотації, ключових слів, шапки, UDC і джерел — контракт v1.9

### Анотація / Abstract

- Після назви статті стоїть рівно один порожній абзац.
- Українська форма: `Анотація.`; англійська: `Abstract.`. Лише мітка напівжирна.
- Після крапки — один пробіл; перше слово тексту починається з великої літери.
- Увесь абзац має стиль `Normal` (`a0`) і звичайний first-line indent шаблону; це не заголовок і не елемент TOC.
- Варіанти `Анотація:`, `АНОТАЦІЯ`, `ABSTRACTS.` та `ANNOTATION:` нормалізуються без переписування змісту.

### Ключові слова / Keywords

- Українська форма: `Ключові слова:`; англійська: `Keywords:`. Лише мітка напівжирна.
- Після двокрапки — один пробіл. Перше ключове слово починається з малої літери, крім абревіатури/коду, що нормативно пишеться великими літерами.
- Абзац має стиль `Normal`, звичайний first-line indent і не входить до TOC.

### Шапка автора

- Email, телефон і Telegram/Viber/WhatsApp видаляються до вставлення у журнал. ORCID зберігається.
- Якщо контакт стоїть окремим рядком, рядок видаляється повністю; порожній абзац на його місці не залишається. Якщо контакт змішаний із корисними даними, видаляється лише контактний фрагмент.
- ПІБ має стиль `AUTOR`; ступені, ролі, установи, місто/країна й ORCID — `pip`.
- Українські назви ролей/статусів у метаданих починаються з малої літери (`студент`, `здобувачка`, `аспірант`, `кандидат наук`, `доцент`, `професор` тощо).
- `pip` не має outline level і не входить до змісту.

### UDC

- Якщо UDC відсутній, збірка зупиняється зі статусом `UDC_LOOKUP_REQUIRED`.
- Назва, анотація, ключові слова та офіційна секція передаються онлайн-агенту для evidence-based пошуку UDC; відповідь містить джерела, confidence, альтернативи та `needs_operator_review: true`.
- Вставлення дозволене лише після підтвердження оператора.
- UDC має фактичний стиль `UDC`; після нього рівно один порожній абзац — не нуль і не більше одного.

### Реконструкція джерел і посилання

- Ручні числа `1.`, `2)` або `(3)` і автоматичне `numPr` є межами нових записів. Ненумерований абзац після запису вважається продовженням, приєднується через один пробіл, а зайвий Enter-абзац видаляється.
- Якщо межі неможливо визначити надійно, збірка зупиняється з `REFERENCE_BOUNDARIES_AMBIGUOUS`.
- Перед застосуванням `REFER` весь запис очищується як після `Ctrl+Space`: без чужих character styles, тіней, підкреслень, hyperlink blue, tab stops, direct indents і source `numId`.
- Кожний звичайний `http/https` має безпосередню мітку `URL: `. DOI URL або bare DOI має мітку `DOI: `. Подвійні/помилкові мітки нормалізуються.
- Кожна стаття отримує окремий numbering instance і починає список з 1.

### Що спрацювало / що вилучено

- Спрацювало: точне копіювання style nodes із `Jurnal.dotx`, structural styleId/outline audit, реконструкція references за межами записів, Ctrl+Space-equivalent rebuild, render усіх сторінок.
- Вилучено як хибне: ручне відтворення стилю `SECTION` «на око»; правило про нульовий відступ для annotation/keywords; довіра до source numbering або до самого факту призначення `REFER`; мовчазна вставка статті без UDC.

## v2.1 body-list and TOC rule
Body lists are part of the article body and must preserve the author's structure. Do not rebuild them unless they are inside the references block. Multi-article drafts must contain a table of contents at `TABLE OF CONTENTS`; page numbers are verified by render-based pagination and then updated.

## v2.3 TOC business rule
The TOC must be built like the published PDFs: centered section row, then for each article: `N.` + author(s) + page on one row, title on the next row. Equal-width columns and one-row article entries are invalid even if a 3-column table exists.


## v2.5 full-release TOC author/page rule

For full journal releases, the TOC is generated only after rendering and page detection that excludes TOC-title occurrences. TOC author cells use a cleaned author map and may contain only participant names. Roles, institutions, degrees, ORCID, locations and contacts must not leak into TOC author cells.

## Область застосування пакета

Скіли NAUKAINFO Agent Skills застосовуються лише в межах проєкту «Дирежор» / NAUKAINFO Journal Builder. Не переносити ці правила на інші чати або документи поза цим проєктом без прямої команди користувача.


## v2.6 scope and frontmatter update

- NAUKAINFO skills are project-scoped: only Дирежор / NAUKAINFO Journal Builder, only after activation in the current chat.
- Header cleanup now removes personal emails, damaged email fragments, phone/contact lines and author-written section notes without leaving blank paragraphs.
- Frontmatter normalization enforces DOI/UDC → cleaned header → title → annotation, while preserving the author body after annotation.


### v2.7 Numbering definition fidelity
Author body lists must preserve original numbering definitions. A bullet list cannot become a decimal list during merge. Do not change author body text to work around numbering; copy/remap numbering.xml definitions safely. References remain the only permitted rebuild exception and must restart at 1 per article.


## v2.8 — Critical fidelity hotfixes

Status: full release v2.6/v2.8 is not considered publishable until the new gates pass on all 24 source articles.

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

## v2.9 — media, multilingual markers, and backups

- Author body text and author count are immutable except explicitly approved service normalization.
- Legacy DOC conversion must be checked against source rendering; omitted embedded images are recovered from source OLE streams, never recreated.
- Every figure object paragraph uses `РИС`; every multilingual figure caption, including captions inside shapes, uses `РисПід`.
- A standalone unnumbered `Таблиця`/`Table`/`Tabelle` is formatted as a table marker without inventing a number.
- Reference headings are language-aware: Ukrainian stamp for Ukrainian articles, `REFERENCES` for English, `LITERATURVERZEICHNIS`/`QUELLENVERZEICHNIS` for German where applicable.
- Numbered variants such as `14. Список використаних джерел` are markers, not body headings; the number is removed only as service formatting and the entries become a fresh `REFER` list from 1.
- TOC author rows are regenerated from final `AUTOR` paragraphs. Roles/degrees never appear as authors; no coauthor may be omitted.
- Previous releases, skills archives, source archives, and QA reports remain immutable versioned backups.

## v3.0 confirmed business rules

- Preserve the complete ETALON section-break/footer/page-number graph; the final journal must retain visible template pagination.
- Every article begins on a new page through `pageBreakBefore` on its first structural paragraph, not through a dummy blank paragraph.
- Annotation/Abstract and Keywords are adjacent; exactly one empty paragraph follows Keywords.
- Exactly one empty paragraph precedes a table/figure cluster after ordinary body text and one follows the completed cluster/source note.
- Figure/table captions inside shapes/textboxes are semantically styled by recursive OOXML inspection.
- Author body run emphasis is protected evidence.
- A missing terminal bibliography heading may be inferred only from strong end-of-article citation evidence.
- Leading spaces/tabs used as fake body indents are removed without modifying lexical text.
- When free listeners exist, `FREE LISTENERS` is the final TOC section and contains every verified listener record.


## Single skill rule

The public activation name is `journal` / «журнал». All former rules are internal modules. No module may be applied in another project/chat without explicit activation of the master skill.


---

# FILE: docs/JOURNAL_CONTRACT.md

# Контракт журналу NAUKAINFO

## Джерела істини

1. Excel/manifest — учасники, назви статей, секції, порядок.
2. Raw articles — зміст і авторське оформлення.
3. `ETALON-JOURNAL.docx` / `Jurnal.dotx` — обкладинки, службові сторінки, колонтитули, поля, page setup, стилі оболонки.
4. Перевірений section library — офіційний порядок секцій.
5. Project memory — відомі проблеми, рішення та регресії.

## Безпека шаблону

- Ніколи не зберігати поверх ETALON.
- Перед build створити byte-for-byte copy у workspace.
- Зберігати обкладинки, headers/footers, numbering, section settings і фінальні сторінки.
- Не замінювати глобально `styles.xml` автора без явного контрольованого режиму.

## Структура статті

```text
DOI (якщо є)
УДК / UDC
порожній службовий абзац
ПІБ авторів
ступені / посади / установи / місто / країна / ORCID
назва статті (може бути багаторядковою)
тіло статті
таблиці / рисунки / формули
список використаних джерел
```

## Мінімальна автентичність — режим за замовчуванням

Дозволено:
- основний текст: 11 pt;
- міжрядковий інтервал: 1.0 / single;
- текст таблиць: 11 pt, single, без first-line indent;
- текст shapes/textboxes: 11 pt, single;
- обережне вирівнювання таблиць, рисунків і підписів;
- видалення контактних даних із шапки як дозволене очищення, якщо цей режим явно активовано;
- службові виправлення, підтверджені оператором.

Не дозволено без окремого рішення:
- переписувати тіло статті;
- змінювати жирність/курсив/наголоси автора масово;
- переставляти абзаци тіла;
- видаляти змістовний текст;
- губити numbering references;
- змінювати геометрію figures/shapes без потреби.

## Таблиці

- Таблиця повинна вміщуватися в printable width, але зміна ширини має бути мінімальною.
- У клітинках немає абзацного відступу першого рядка, якщо такого немає в оригіналі; проєктний default — 0.
- Перевіряється **ефективний** відступ: direct paragraph property → paragraph style → base-style chain → document default. Значення `None` у direct property не означає нуль.
- Якщо ETALON `Normal` містить first-line indent, а source table — ні, у кожному цільовому table paragraph ставиться прямий `w:firstLine="0"`; глобальний `Normal` не змінюється.
- Шрифт 11 pt, single.
- Для кожної таблиці source↔target звіряються: точний текст, paragraph/run order, alignment, line/paragraph spacing, bold/italic/underline, font size, vertical alignment, margins, widths, row heights, merged cells, row splitting і repeating headers.
- Не перетворювати складні/merged таблиці без visual check.
- Примітка або джерело під таблицею може бути italic лише коли так подав автор або це погоджене правило.
- Після save/re-open не повинно залишатися нез’ясованих table-format differences; усі сторінки з таблицями обов’язково рендеряться й переглядаються.

## Рисунки і shapes

- Зберігати anchors, wrap, size, group relationships, captions.
- Перевіряти не лише кількість objects, а й геометрію та сторінку розташування.
- Textbox text — 11 pt, single.

## References

- Кожна стаття має власну нумерацію, починаючи з 1.
- Не переносити numbering relationship між статтями.
- Не втрачати list labels під час вставки у master shell.
- Заголовок і entries перевіряються окремо.

## Секції і page breaks

- Не створювати секцію, якщо в ній немає жодної статті.
- Кожна стаття починається з нової сторінки.
- Structural, section, template та article-start page breaks зберігаються безумовно.
- Авторські внутрішні page breaks за замовчуванням зберігаються, але після зміни 14→11 pt ручні pagination-helper breaks біля таблиць потрібно повторно оцінити.
- Кандидат можна прибрати лише після порівняльного render-аудиту: таблиця має або вміститися повністю, або ділитися не грубіше за приблизне співвідношення 60/40 за обсягом; 70/30 чи малий залишковий фрагмент не допускаються без рішення оператора.
- Якщо призначення розриву, геометрія таблиці або близькість до межі 60/40 неоднозначні, розрив зберігається і ставиться `needs_operator_review`.
- Хвостові порожні абзаци перед builder-inserted break — низько/середньо пріоритетний cleanup, не причина зупиняти діагностичну збірку.

## Структурне місце вставки в ETALON

- Місце вставки визначається структурно, а не за номером абзацу.
- Після заголовка `TABLE OF CONTENTS` зберігається сторінка змісту та її page break.
- Статті вставляються безпосередньо перед paragraph-level `w:sectPr`, який починає захищену хвостову сторінку.
- Таким чином перша стаття починається на наступній сторінці після змісту, а хвостова службова сторінка залишається останньою.
- Для копіювання використовуються повні OOXML body elements із relationships/styles/numbering/media, а не plain text.


## Paragraph role contract

Ordinary body prose, annotation/abstract paragraphs and keywords paragraphs use the authoritative ETALON `Normal` 1 cm first-line indent. All service metadata, author/title blocks, drawing paragraphs, figure/table captions and notes, table-cell text, numbered/bulleted items, reference heading and reference entries must resolve to zero positive first-line indent. Hanging reference indentation is permitted.

Editable SmartArt/shapes/textboxes are protected content objects. A valid build preserves their text signatures, OOXML relationships, geometry and editability.


## Canonical section and style application (v1.5)

- Section headings in the journal body are English-only, resolved by `section_id` from the official project section library, inserted once before the first article of a non-empty section, and styled `SECTION`.
- For the Hnysiuk article in conference 136, section 1 is verified as `ECONOMIC THEORY, MACRO- AND REGIONAL ECONOMY`.
- The final DOCX must contain actual style IDs: DOI/UDC=`UDC`, human names=`AUTOR`, author metadata=`pip`, title=`Назва1`, drawing paragraph=`РИС`, figure caption=`РисПід`, table cells=`TABLETEXT`, reference heading=`REF-TITLE`, reference entries=`REFER`.
- A visually similar result with `Normal` style is a build failure. Style assignment is followed by reopen audit and full render.

## Caption and reference contract v1.6

### Table/figure semantic formatting

- Table number: separate paragraph above title, right aligned, bold, 11 pt, single, firstLine=0, keep with next.
- Table title: next non-empty paragraph, centered, bold, 11 pt, single, firstLine=0, keep with table.
- Table cell paragraphs: actual style `TABLETEXT`, no positive first-line indent, source alignment/emphasis preserved.
- Figure/SmartArt paragraph: actual style `РИС`; caption below: actual style `РисПід`.
- Source notes under tables/figures: 11 pt, single, firstLine=0, source emphasis preserved.

### Reference block

- Ukrainian stamp is exactly `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`.
- Exactly one blank paragraph before the stamp and exactly one blank paragraph after it.
- Stamp style is `REF-TITLE`; entries use `REFER`.
- Each article receives a fresh decimal numbering instance restarted at 1.
- Copied direct indents/tabs/foreign `numId` must not override ETALON hanging geometry (567 twips left/hanging).
- Rendered continuation lines must align with reference text; bullets/arrows/tab artifacts are prohibited.


## v1.7 spacing and TOC gate

A build is rejected if any of the following is true:

- no empty paragraph after article title;
- no empty paragraph after a table/source-note block;
- no empty paragraph after a figure/source-note block;
- no empty paragraph after `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`;
- `pip`, DOI/UDC, reference entries, captions, table text, or body paragraphs have an outline level;
- references contain copied character formatting, hyperlink underline/color, foreign list definitions, manual tab stops, or numbering that does not restart at 1 per article.


## Multi-article assembly gate v1.8

- Inputs are validated article ranges, not complete single-article journal shells.
- Every article after the first receives an explicit article-start page break; section headings are not duplicated for consecutive articles in the same section.
- Each reference block must use a distinct numbering instance with `startOverride=1`; the first visible label in every article is `1.`.
- TOC page numbers are materialized only after final pagination and verified against rendered internal page numbers.
- Source↔final exact text/table block signatures and object/media signatures must match for every article.
- The protected tail remains last; no trailing blank page or foreign section properties are permitted.


## Semantic front-matter and bibliography gate v1.9

- Exactly one blank follows the actual UDC line; missing UDC blocks the build until an online evidence-based proposal is operator-approved.
- Exactly one blank follows the article title. Annotation/abstract and keywords are `Normal` paragraphs, not headings.
- Canonical labels: bold `Анотація.` / `Abstract.` plus one space and uppercase body start; bold `Ключові слова:` / `Keywords:` plus one space and lowercase first keyword unless it is an acronym.
- Email/phone/messenger contacts are removed from the author header without blank holes; ORCID remains; Ukrainian role/common-noun metadata begins lowercase.
- Manual reference numerals and Enter-split continuation paragraphs are reconstructed into logical entries before `REFER` is applied. Ambiguous boundaries stop the build.
- Every ordinary web link is prefixed `URL: `; DOI URLs and bare DOI identifiers are prefixed `DOI: `.
- The entire reference entry is rebuilt with Ctrl+Space-equivalent plain formatting, then assigned a fresh per-article list starting at 1.
- Exact style definitions for `SECTION`, `AUTOR`, `Назва1`, `pip`, `UDC`, `REF-TITLE`, `REFER` and supporting styles are copied from the supplied `Jurnal.dotx`; a hand-made approximation is forbidden.

## Critical body-integrity contract v2.0

- Author-body lexical content must be identical after the narrow allowed-normalization whitelist.
- Author-body structural similarity must be at least 0.99.
- Paragraph order, manual/automatic list mode, table rows/cells, figures, formulas, captions and object order are protected.
- A build with any unapproved body difference cannot pass quality gate.
- References may be renumbered per article; ordinary body lists may not be converted.


## v2.2 TOC/front-matter update
- TABLE OF CONTENTS is a real 3-column Word table, not loose paragraphs.
- TOC generation scans canonical styles only: `SECTION`, `AUTOR`, `Назва1`; output styles are `Tab_SEC`, `Tab_PIP`, `Tab_Taitl`.
- Article front matter is normalized to DOI/UDC -> author header -> one blank -> title -> one blank -> body.
- Split source titles are merged; duplicate title paragraphs created by the builder are prohibited.
- Page numbering from ETALON must be preserved by keeping the numbered middle section break before the final service page.

## v2.3 TOC contract
The table of contents must visually match the published NAUKAINFO PDFs. It is a borderless 3-column table: narrow number column, wide content column, narrow page column. Section rows are merged across all columns and use `Tab_SEC` (`TabSEC`). Every article uses two rows: number/author/page row (`Tab_Taitl`, `Tab_PIP`, right-aligned `Tab_Taitl`) followed by a blank/title/blank row (`Tab_Taitl`). Article title must not share a row with the author.


## v2.5 full-release TOC author/page rule

For full journal releases, the TOC is generated only after rendering and page detection that excludes TOC-title occurrences. TOC author cells use a cleaned author map and may contain only participant names. Roles, institutions, degrees, ORCID, locations and contacts must not leak into TOC author cells.


## v2.6 scope and frontmatter update

- NAUKAINFO skills are project-scoped: only Дирежор / NAUKAINFO Journal Builder, only after activation in the current chat.
- Header cleanup now removes personal emails, damaged email fragments, phone/contact lines and author-written section notes without leaving blank paragraphs.
- Frontmatter normalization enforces DOI/UDC → cleaned header → title → annotation, while preserving the author body after annotation.


### v2.7 List/numbering contract
For all non-reference author body paragraphs with `w:numPr`, final DOCX must preserve resolved `numFmt`, `lvlText`, list level, and visual marker from the source article. Multi-article assembly must allocate fresh `numId` values where needed to avoid collisions.


## v2.8 — Critical fidelity hotfixes

Status: full release v2.6/v2.8 is not considered publishable until the new gates pass on all 24 source articles.

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

## v2.9 release integrity additions

### Object and caption contract
- All visible source figures must exist in the final journal in the same order and with matching media bytes/hash where the source part is recoverable.
- Drawing/object paragraphs: `РИС` (`ad`). Captions: `РисПід` (`af6`), including `Abb.`, `Figure`, `AGD1`, and captions inside textboxes.
- No object may be clipped or extend beyond printable margins.

### Table marker contract
- Numbered and unnumbered table markers are valid. A missing author number is preserved; it is not synthesized.

### References contract
- Reference marker recognition is multilingual and language-specific.
- All lists restart at 1 per article/block and preserve source entry order/content.

### TOC contract
- Rebuild after final author-header classification.
- TOC author text must exactly match ordered final `AUTOR` paragraphs for each title.

## v3.0 release gates

A release fails when: ETALON section count/footer/page-number signature changes; any article lacks `pageBreakBefore`; a break-only paragraph remains inside an article; annotation/keywords spacing is wrong; a source media object is absent; nested textbox/table content is unstyled or outside margins; author bold/italic emphasis is lost; listener count differs between manifest and TOC; or visible page numbers are absent after render.


## V3.1 master-skill integrity gate

The release decision is per article. Each source must be compared to its final article region for lexical text, paragraph order, run emphasis, list definitions, tables, media/object hashes, nested shape text and author count. Unknown differences block the release. PDF-only text extraction is not sufficient when native DOC/DOCX or object-level evidence exists.


---

# FILE: skills/journal/SKILL.md

---
name: journal
description: Єдиний проєктний скіл для повного циклу NAUKAINFO Journal Builder у проєкті «Дирежор»: приймання матеріалів, підготовка статей, збирання журналу в ETALON, збереження авторського тексту/форматування/об’єктів, зміст, нумерація сторінок, рендер, глибокий аудит і реліз. Активується лише явно в цьому проєкті та чаті.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; lxml; LibreOffice; NAUKAINFO Journal Builder.
metadata:
  author: naukainfo
  version: "3.2.0"
  priority: "0-critical"
  scope: "Дирежор / NAUKAINFO Journal Builder only"
---

# ЖУРНАЛ — єдиний головний скіл

## Нульовий gate: обов’язкові виробничі активи

Перед читанням архіву статей або будь-якою генерацією виконавець зобов’язаний знайти у переданій папці такі точні активи:

- `02_TEMPLATES_REQUIRED/ETALON-JOURNAL.docx`;
- `02_TEMPLATES_REQUIRED/Jurnal.dotx`;
- `01_SKILL_JOURNAL/NAUKAINFO_Agent_Skills_v3_2.zip` або розпакований `skills/journal/SKILL.md`;
- `03_REFERENCE_RELEASES/JOURNAL_136_FINAL_RELEASE_v33.docx` як regression reference, не як джерело контенту;
- `05_TESTS_QA_AND_SCHEMAS/FILE_MANIFEST.json`;
- вхідний архів/папку статей і manifest.

Якщо ETALON, Jurnal.dotx, manifest або головний скіл не знайдені чи не відкриваються, збірку **не починати**. Вивести тільки:

`BUILD BLOCKED: REQUIRED_ASSET_MISSING`

із переліком відсутніх активів. Заборонено створювати обкладинку, стилі, зміст, секції, колонтитули або master document «з нуля» чи приблизно відтворювати їх за пам’яттю.

До запуску перевірити `ETALON-JOURNAL.docx`:

- рівно 3 `w:sectPr`;
- друга секція має `w:pgNumType w:start="1"`;
- наявний footer reference у секції з основним текстом;
- наявні styleId: `SECTION`, `AUTOR`, `pip`, `11`, `UDC`, `TabSEC`, `TabPIP`, `TabTaitl`, `TABLETEXT`, `REF-TITLE`, `REFER`, `ad`, `af6`.

Для цього використовувати `scripts/preflight_required_assets.py`. Будь-який FAIL = `BLOCKED`, а не імпровізація.


## Активація і межі

Цей скіл не є глобальним. Він працює лише одночасно за трьох умов:

1. поточний проєкт — **«Дирежор» / NAUKAINFO Journal Builder**;
2. користувач у цьому чаті явно активував роботу зі скілом «журнал» або доручив збирання/перевірку журналу;
3. поточне завдання стосується саме цього журналу.

В інших чатах і проєктах діяти за локальними інструкціями того чату та стандартними правилами, не читати й не оновлювати цей пакет.

## Абсолютний пріоритет

Авторське тіло статті є джерелом істини. Заборонено без явного дозволу:

- переписувати, скорочувати, доповнювати, переставляти або перекладати текст;
- змінювати кількість авторів;
- втрачати абзаци, слова, таблиці, рисунки, формули, фігури, SmartArt, text box, підписи, примітки чи джерела;
- змінювати ручні списки на автоматичні або навпаки, крім блоку references;
- знімати авторське жирне/курсивне/підкреслене виділення, верхній/нижній індекс або вирівнювання підзаголовків тіла;
- приймати «візуально схоже» або «кількість об’єктів збігається» як доказ цілісності.

Дозволені лише затверджені службові правки: UDC/УДК, очищення шапки від контактів, AUTOR/pip, назва, стандартні мітки анотації/keywords/references, канонічні підписи таблиць і рисунків, службові порожні абзаци, розриви та стилі без зміни змісту.

## Заборона точкового коду

У виробничих скриптах не повинно бути прізвищ авторів, назв конкретних статей або умов типу «відновити рисунок Тодорової». Конкретні статті можуть бути лише regression fixtures. Основний алгоритм працює для **кожної** статті через manifest і однакові gates.

## Єдиний конвеєр

### 0. Бекап і джерела істини

- Не перезаписувати оригінали, ETALON, попередній реліз або попередній ZIP скілів.
- Джерела істини: Excel/manifest, сирі авторські DOC/DOCX, ETALON/Jurnal.dotx, явні метадані.
- Для кожної статті створити source manifest: автори, назва, секція, мова, тип участі, вихідний файл і hash.

### 1. Глибокий source snapshot для кожної статті

До будь-яких змін зберегти:

- видимий текст у порядку документа, включно з таблицями, `w:txbxContent`, VML/DrawingML text box;
- абзаци, runs і їх bold/italic/underline/superscript/subscript/alignment;
- ручні й автоматичні списки та `numId → abstractNumId → numFmt → lvlText`;
- таблиці: рядки, клітинки, merge map, ширини, text/paragraph formatting;
- рисунки, media bytes/hash, relationship IDs, extent, crop, anchor/inline, order;
- shapes, SmartArt, charts, equations, OLE, captions and source notes;
- section/page-break signature.

### 2. Підготовка статті

Застосувати тільки підтверджені правила внутрішніх модулів:

- шапка: DOI/UDC → AUTOR/pip → blank → title → blank → body;
- email/phone/messenger видаляються лише з шапки; ORCID зберігається;
- author-written section notes видаляються;
- `Анотація.`/`Abstract.` та `Ключові слова:`/`Keywords:` нормалізуються без зміни тексту;
- між анотацією і keywords немає blank; після keywords рівно один blank;
- table/figure/caption/source blocks нормалізуються без first-line indent;
- recursively обробляти text boxes/shapes/nested tables;
- references розпізнавати маркером або сильними terminal-list ознаками, але невпевненість = stop/review;
- legacy `.doc` спочатку render/convert/audit, щоб не загубити OLE images.

### 3. Вставка в ETALON

- ETALON є master shell; не будувати документ заново.
- Зберегти секції, footer, page-number fields, front/tail pages і захищену фінальну сторінку.
- Кожна стаття починається через `pageBreakBefore`; не використовувати dummy blank/page-break paragraph між статтями.
- Секції й статті йдуть лише в manifest order.

### 4. Після кожної вставленої статті — обов’язковий per-article audit

Порівнювати `raw source → normalized article → final journal region` окремо для кожної статті:

1. **Lexical:** нуль непогоджених deletions/replacements/insertions.
2. **Paragraph/order:** порядок і кількість змістових абзаців збережені; дозволені blanks обліковуються окремо.
3. **Run formatting:** авторські emphasis/alignment signatures збережені.
4. **Lists:** manual/automatic mode і numbering definition semantics збережені; references — окрема дозволена реконструкція.
5. **Tables:** текст усіх клітинок, merges, order і table count збережені.
6. **Objects:** images/shapes/charts/formulas/OLE/captions/media hashes/order збережені.
7. **Nested content:** текст і таблиці всередині фігур не пропускаються.
8. **Author count:** source authors = manifest authors = final AUTOR = TOC authors.

PDF-only порівняння є fallback, а не достатнім доказом. Для legacy `.doc` потрібні source render + converted DOCX + final render.

### 5. Глибокий текстовий gate

Запустити `scripts/deep_text_integrity_audit.py` для всіх статей. Дозволені зміни задаються явним whitelist. Будь-який невідомий diff:

- переводить реліз у `BLOCKED`;
- показує article index, source range, final range і контекст;
- не може бути перекритий LLM-впевненістю або візуальним оглядом.

Текст усередині растрів/скріншотів не можна оголосити перевіреним за XML. Його цілісність підтверджується object hash/render comparison або ручним review, і в звіті це позначається окремо.

### 6. TOC і вільні слухачі

- TOC будується лише після стабілізації тіла і пагінації.
- Реальна 3-column Word table за PDF-contract.
- Автори в TOC — лише імена, синхронізовані з body/manifest.
- FREE LISTENERS завжди фінальна TOC section, якщо manifest містить вільних слухачів.
- Page numbers визначаються після рендеру, потім TOC матеріалізується і документ рендериться повторно.

### 7. Render gate

Після кожної значущої серії правок:

1. render DOCX → PNG/PDF;
2. переглянути **кожну** сторінку при 100%;
3. перевірити таблиці, clipping, figures, captions, page numbers, section transitions, blank pages;
4. після TOC/page updates — повторний render і повторний повний огляд.

### 8. Фінальний fail-closed quality gate

`PASS` можливий лише коли одночасно:

- усі статті mapped до джерел;
- confirmed unapproved text changes = 0;
- confirmed missing paragraphs/tables/objects/captions/formulas = 0;
- author count mismatches = 0;
- run-emphasis mismatches = 0;
- numbering-definition mismatches = 0;
- ETALON section/page-number signature збережена;
- article starts і TOC pages правильні;
- full render review passed;
- всі дозволені зміни перелічені у звіті.

Якщо хоча б один із цих пунктів не доведений, статус — `REVIEW` або `BLOCKED`, але не `PASS`.

## Внутрішні модулі

Інші файли `skills/naukainfo-*/MODULE.md` є внутрішньою бібліотекою правил цього скілу і не активуються самостійно. Головний скіл підтягує їх за ситуацією:

- fidelity: author body, media/object, shapes/textboxes, tables, numbering, headings;
- front matter: UDC, author header, AUTOR/pip, title, annotation/keywords;
- references: marker language, terminal inference, entry reconstruction, numbering restart;
- layout: ETALON insertion, sections/page numbers, article page starts, spacing;
- TOC: table contract, author sync/cleaning, free listeners;
- release: backups, render, deep audits, quality gate, changelog.

## Артефакти релізу

- final journal DOCX;
- final QA JSON;
- per-article text/run/table/object audit JSON;
- render evidence summary;
- versioned skills ZIP + changelog;
- короткий звіт: що виправлено, що спрацювало, що видалено з активної логіки.

## Done when

Реліз доведено на рівні **кожної статті**, а не лише всього документа: нуль непогоджених текстових змін, нуль втрат об’єктів і авторів, збережені авторські emphasis/list semantics, правильні ETALON pagination/TOC, і всі сторінки переглянуті після останнього рендеру.


---

# FILE: skills/naukainfo-agent-orchestrator/MODULE.md

---
name: naukainfo-agent-orchestrator
description: Orchestrates an end-to-end NAUKAINFO journal run by selecting context, intake, article inspection, UDC review, normalization, assembly, DOCX audit, visual regression, quality gate, and memory skills. Use when the user asks to scan, build, test, diagnose, or finalize an entire conference journal.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.1.0"
---

# Workflow

Progress:
- [ ] Load project context
- [ ] Run preflight
- [ ] Scan conference
- [ ] Resolve ambiguous files/articles
- [ ] Create and validate decision bundle
- [ ] Present plan and request build approval
- [ ] Build on workspace copies
- [ ] Run DOCX/content/object audits
- [ ] Run visual regression
- [ ] Run quality gate
- [ ] Update project memory

## Routing

- Context/code question → `naukainfo-project-context`.
- Files/Excel/matching → `naukainfo-conference-intake`.
- Ambiguous DOCX/header/title → `naukainfo-article-structure`.
- Missing UDC → `naukainfo-udc-review`.
- Formatting copy → `naukainfo-minimal-normalization`.
- Table placement/source fidelity after ETALON insertion → `naukainfo-table-format-fidelity`.
- Paragraph-role and no-indent routing → `naukainfo-semantic-style-routing`.
- SmartArt/shapes/textboxes → `naukainfo-shape-object-fidelity`.
- Draft build → `naukainfo-journal-assembly`.
- Structural/content checks → `naukainfo-docx-audit`.
- PDF/JPEG comparison → `naukainfo-visual-regression`.
- Release decision → `naukainfo-quality-gate`.
- Lessons learned → `naukainfo-project-memory`.

## Plan-validate-execute

For every state-changing operation:
1. Produce a structured plan.
2. Validate paths, hashes and decision bundle.
3. Ask for approval.
4. Execute one stage.
5. Audit before continuing.

Do not collapse all stages into one opaque call.


---

# FILE: skills/naukainfo-annotation-keywords-normalization/MODULE.md

---
name: naukainfo-annotation-keywords-normalization
description: Normalizes Ukrainian and English annotation/abstract and keywords opening labels without changing the article meaning: ordinary Normal paragraph geometry, bold label only, canonical punctuation, and language-aware first-letter casing. Use after title/style application and before content-integrity QA.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; OOXML/python-docx; NAUKAINFO Jurnal.dotx.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Annotation / abstract contract

1. The annotation is normally the first non-empty body paragraph after the article title and the required one blank paragraph.
2. Ukrainian canonical opening: **`Анотація.`** followed by exactly one space and body text beginning with an uppercase letter.
3. English canonical opening: **`Abstract.`** followed by exactly one space and body text beginning with an uppercase letter.
4. Only the opening label is bold. The annotation body is regular.
5. The paragraph uses the authoritative template `Normal` style (`a0` in the verified template), not a heading style. It retains the ordinary body first-line indent and must not enter the TOC.
6. Normalize variants such as `Анотація:`, `АНОТАЦІЯ`, `ABSTRACTS.`, or `ANNOTATION:` without rewriting the body.

# Keywords contract

1. Ukrainian canonical opening: **`Ключові слова:`** followed by exactly one space.
2. English canonical opening: **`Keywords:`** followed by exactly one space.
3. Only the label is bold. The keyword sequence is regular.
4. The first keyword starts with a lowercase letter unless the first token is an acronym/proper code that is conventionally uppercase (AI, HR, NATO, UDC, etc.).
5. The paragraph uses template `Normal`, is not a heading, and must not enter the TOC.
6. Preserve the author’s keyword sequence and punctuation except the required label/punctuation/casing repair.

# QA

- Compare source and final body text after removing only the normalized label punctuation/case.
- Assert one blank paragraph after the title and no unexpected blank between annotation and keywords.
- Inspect run properties: label run bold; body run not forced bold.
- Render the first page of every article and verify visual indentation and label emphasis.

Use `scripts/finalize_business_semantics.py` as the deterministic implementation.

## v3.0 exact adjacency

Treat annotation/abstract and keywords as one front-body cluster: annotation is immediately followed by keywords with zero empty paragraphs. Insert exactly one empty paragraph after the complete keywords paragraph before the first ordinary body paragraph. This overrides any source blank between annotation and keywords while preserving all lexical content.


---

# FILE: skills/naukainfo-article-structure/MODULE.md

---
name: naukainfo-article-structure
description: Inspects DOCX or converted workspace copies read-only to identify UDC/DOI, authors, affiliations, title, body start, references, tables, images, formulas, shapes, and suspicious service-form structure. Use when a title is multiline, a header is ambiguous, or matching needs evidence.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Procedure

1. Call `inspect_docx_readonly` on the source or workspace copy.
2. Read the first front-matter paragraphs plus table cells, not the full article unless necessary.
3. Identify:
   - DOI and UDC;
   - human author names;
   - degree/position/institution/city/country/ORCID;
   - complete multi-paragraph title;
   - body boundary;
   - references heading and list behavior;
   - object counters.
4. Classify uncertain lines as `unknown`, not automatically as affiliation.
5. Return evidence with paragraph indices and exact short excerpts.

## Hard distinctions

- `author`: human name only.
- `affiliation`: degrees, positions, institutions, locations, ORCID and other service metadata.
- A university named after a person is still an institution.
- Text after the title is not header unless there is strong structural evidence.
- Application/participant form tables are service documents even when they contain a presentation title.

Read `references/front-matter.md` for detailed rules.


---

# FILE: skills/naukainfo-author-body-fidelity/MODULE.md

---
name: naukainfo-author-body-fidelity
description: Highest-priority NAUKAINFO publishing skill. Preserves the author's article body text, paragraph order, lists, tables, figures, formulas, captions, notes, and object structure one-to-one while allowing only explicitly approved journal normalization. Must run before and after every formatting, merge, pagination, or style operation.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; lxml; NAUKAINFO Journal Builder project.
metadata:
  author: naukainfo
  version: "1.0.0"
  priority: "0-critical"
---

# Non-negotiable principle

The author body is the source of truth. Do not rewrite, paraphrase, shorten, expand, reorder, “improve,” translate, or silently correct the scientific text. The target is:

- **100% lexical preservation of the article body**, except explicitly approved label-only normalizations;
- **at least 99% structural preservation** of paragraphs, lists, tables, figures, formulas, captions, notes, and object order;
- when layout convenience conflicts with author-content fidelity, **author-content fidelity wins**.

# Scope

The protected author body begins after the article title/required blank and includes annotation/abstract, keywords, main text, all lists, tables, drawings, SmartArt/shapes, formulas, captions, notes/sources, conclusions, and bibliography entries. UDC/DOI and the author header are service metadata and follow separate skills, but their removal or normalization must never shift or delete body content.

# Allowed changes only

1. Set the approved font size and line spacing.
2. Assign canonical template styles to recognized semantic roles without changing visible wording or order.
3. Normalize only the labels explicitly defined by business rules: `Анотація.` / `Abstract.`, `Ключові слова:` / `Keywords:`, reference stamp, `URL:` / `DOI:` prefixes.
4. Remove personal contact data from the author header only, without blank holes.
5. Normalize service metadata grammar in the author header only.
6. Apply approved UDC/DOI insertion, table/figure spacing, first-line-indent fixes, and pagination repair that do not alter the body text or object order.
7. Reconstruct bibliography numbering only inside the reference block; bibliography entry wording must remain intact.

Anything else requires an explicit operator decision recorded in the audit trail.

# Body-list preservation rule

- A manually typed body list (`1.`, `2.`, `-`, `•`, arrows, letters) remains manually typed unless the user explicitly authorizes conversion.
- An automatic Word list remains automatic and retains its numbering semantics.
- Never convert a manual body list into automatic numbering merely for visual neatness.
- Reference lists are the only default exception because `REFER` requires fresh per-article numbering from 1.

# Procedure

1. Snapshot the raw article before editing:
   - ordered paragraph texts;
   - paragraph/list markers and numbering mode;
   - tables with row/cell text and merge map;
   - drawings, SmartArt, shapes, textboxes, equations, footnotes/endnotes and captions;
   - object order and relationship/media signatures.
2. Classify every intended change as `allowed`, `operator-approved`, or `forbidden`.
3. Apply only allowed/approved transformations.
4. Reopen the output and run structural comparison against the raw source.
5. Report separately:
   - lexical body match;
   - paragraph/order match;
   - table/cell match;
   - list-mode match;
   - object/formula match;
   - approved differences.
6. Render every page and visually inspect body flow, tables, lists, drawings, captions and page breaks.
7. Fail the build if any unapproved body change exists.

# Mandatory gates

- `body_text_unapproved_changes == 0`.
- `body_structure_similarity >= 0.99`.
- paragraph and table order unchanged.
- no missing/extra table rows or cells.
- no missing/extra figures, formulas, SmartArt/shapes or captions.
- body manual-vs-automatic list mode unchanged, except references.
- every difference is listed in `approved_transformations` with the rule that authorized it.
- full render QA passed.

# What worked

- Source/final semantic signatures compared after every major operation, not only after final merge.
- Separating service metadata normalization from the protected author body.
- Treating manual body list markers as author text instead of “fixing” them into Word numbering.
- Whitelisting allowed transformations and failing closed on everything else.

# What did not work and is removed from active logic

- “Visually similar” acceptance without text/structure signatures.
- Rebuilding body paragraphs from extracted plain text.
- Automatic grammar or stylistic rewriting of the article body.
- Converting all detected lists to automatic numbering.
- Using object counts alone as proof of fidelity.

# Done when

The source-to-final audit shows no unapproved lexical changes, at least 99% structural fidelity, exact table/list/object order, and every rendered page has passed visual review.

## v2.1 addition: body lists are author structure
Lists inside the body of an article are treated as author structure. They must not be converted between manual and automatic numbering unless the block is identified as the references block. Only `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` is rebuilt with canonical independent numbering. Body lists, even if visually imperfect, stay as the author created them unless the user explicitly asks to normalize them.

## v2.9 non-text extension

The protected author body includes media bytes, object order, captions, subheading emphasis, list-definition semantics, tables, formulas, and author count—not only extracted paragraph text. Any missing image or coauthor is a hard failure.

## v3.0 run-emphasis fidelity

Body integrity includes run-level bold, italic, underline, small caps, superscript/subscript, and paragraph alignment. Scientific subheadings such as `Вступ`, `Мета дослідження`, `Матеріали та методи`, `Результати та їх обговорення`, and `Висновки` must retain the source emphasis unless a canonical marker rule explicitly overrides it. Compare source/final emphasis signatures per paragraph and fail on unexplained loss.


---

# FILE: skills/naukainfo-author-header-cleanup/MODULE.md

---
name: naukainfo-author-header-cleanup
description: Cleans and grammatically normalizes the author header before the article title: removes email/phone/messenger contacts without blank holes, preserves ORCID, routes names/metadata to canonical styles, and lowercases Ukrainian role/common-noun lines. Use before title/body normalization.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; OOXML/python-docx; NAUKAINFO Jurnal.dotx.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Scope

The header is the range after DOI/UDC and before the article title.

# Contact cleanup

- Remove personal email addresses, phone numbers and Telegram/Viber/WhatsApp contact lines.
- ORCID is allowed and must be preserved.
- If a paragraph contains both useful metadata and contact data, remove only the contact token/label and retain the meaningful remainder.
- If the paragraph becomes empty, delete it completely. Do not leave an empty paragraph or double gap.
- Contact removal is permitted editorial cleaning and is not `critical_text_loss`.

# Grammar and capitalization

- Human names use `AUTOR` and retain proper-name capitalization.
- Degree, status, position, institution, city/country and ORCID use `pip`.
- Ukrainian common-noun role/status lines begin with lowercase: `студент`, `студентка`, `здобувач`, `здобувачка`, `аспірант`, `кандидат наук`, `доцент`, `професор`, `керівник`, etc., unless the word begins a full sentence rather than a metadata line.
- Do not invent or expand degrees, positions or affiliations.
- `pip` must have no outline level and must never enter the TOC.

# QA

1. Scan header text for email/phone/contact labels; expect zero prohibited contacts.
2. Confirm ORCID remains.
3. Confirm no blank paragraph was introduced where a contact was deleted.
4. Compare all non-contact header text with the source.
5. Assert exact style IDs and render the header.

Two real project-derived fixtures with contacts are maintained under `tests/fixtures/`.


# v1.1 additions: frontmatter hygiene and contacts

- Remove author-supplied section notes such as `Секція 013 – ...` from the article body/frontmatter; real journal sections are inserted only by the builder as `SECTION` rows.
- Remove personal emails even when they are split or partially damaged by previous processing. Examples: `name@gmail.com`, `name @ ukr.net`, and leftover fragments from email paths such as `nv/`.
- If an `AUTOR` paragraph contains a comma followed by degree/position data, split it into:
  - author name only → `AUTOR`;
  - degree/position/affiliation remainder → `pip`.
- If the source order is `UDC → title → header`, reorder front matter to the journal contract `UDC/DOI → header → title`; record this as allowed frontmatter normalization, not body rewriting.
- Never move or rewrite paragraphs after `Анотація.` / `Abstract.` as part of header cleanup.


---

# FILE: skills/naukainfo-author-heading-emphasis-fidelity/MODULE.md

---
name: naukainfo-author-heading-emphasis-fidelity
description: Preserves author-created body emphasis for section labels such as Introduction, Materials and methods, Results, Conclusions while allowing only journal style assignments that do not remove bold/italic semantics.
version: "2.8.0"
---

# Rule

Body subheadings written by the author, for example `Вступ`, `Матеріали та методи`, `Результати та їх обговорення`, `Висновки`, `Introduction`, `Materials and methods`, `Results`, `Conclusions`, are part of the article body.

If the author made them bold, centered, italic, or otherwise emphasized, that emphasis must remain after normalization and journal insertion.

# Regression lesson

In the Magdysiuk article, body subheadings stayed centered but lost bold. This is a content-fidelity regression, not a cosmetic issue.

# Validation

Compare source and final for each recognized body subheading:

- text exactness;
- paragraph order;
- alignment;
- bold/italic/all-caps emphasis;
- spacing.

Do not convert these body subheadings into TOC headings unless the business plan explicitly says so.


---

# FILE: skills/naukainfo-body-leading-space-normalization/MODULE.md

---
name: naukainfo-body-leading-space-normalization
description: Removes author-created leading spaces or tabs used as fake paragraph indents while preserving the text, paragraph order, and real author formatting.
license: Proprietary project skill
compatibility: Word DOCX/OOXML; NAUKAINFO Journal Builder; Дирежор project only.
metadata:
  author: naukainfo
  version: "3.0.0"
---

# Scope

Some authors simulate a first-line indent by typing multiple spaces or tabs at the beginning of body paragraphs. These characters create unstable layout after style normalization and must be removed without rewriting the sentence.

# Rules

1. Inspect the first visible text node of ordinary body paragraphs, including paragraphs inside textboxes.
2. Remove only leading spaces, non-breaking spaces, and tabs used before the first lexical character.
3. Do not collapse internal spaces, punctuation, equations, code, tables, reference URLs, or intentional alignment inside figures.
4. Delete a paragraph only when it contains no object and consists solely of spaces/tabs, and only if it is not a required business blank.
5. Apply the canonical paragraph/style indent after character cleanup.
6. Compare source/final lexical text after excluding the removed leading whitespace only.

# QA

Fail if a paragraph still begins with 2+ layout spaces/tabs outside an allowed preformatted block, or if any non-whitespace character was removed.

# Worked

Sherbon-type English body paragraphs: remove fake space indentation while retaining wording, emphasis, and paragraph boundaries.

# Removed from active logic

Global whitespace normalization across the whole article, which can damage references, equations, tables, and author punctuation.


---

# FILE: skills/naukainfo-canonical-style-application/MODULE.md

---
name: naukainfo-canonical-style-application
description: Inserts the verified English-only section heading once before the first article of a section and structurally applies the canonical ETALON paragraph styles to UDC/DOI, author names, author metadata, article titles, drawings, figure captions, table cells, reference headings, and reference entries. Use after article insertion and before pagination/visual QA.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; NAUKAINFO ETALON styles; Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "2.0.0"
---

# Purpose

A visually similar article is not sufficient. The final DOCX must contain the actual ETALON styles so later TOC, pagination, audits and automated editing can rely on structural semantics.


# Authoritative style-source rule

Never recreate `SECTION` or any canonical style by visual approximation. Copy the exact style node and its base-style chain from the user-supplied `Jurnal.dotx`. For the verified template, `SECTION` is centered, Times New Roman 24 pt, bold, all caps, 18 pt after, based on Heading 1 and outline level 1 through inheritance. Preserve `pip` as non-heading metadata.

# Section rule

1. Resolve `section_id` from the validated manifest.
2. Resolve the official English label from the project section library; never translate ad hoc.
3. Insert the label once, immediately before the first article in that section.
4. Do not repeat it before subsequent articles of the same section.
5. Do not create empty sections.
6. Apply style `SECTION` and keep it with the following UDC/DOI block.
7. Section headings inside the journal body are English-only.

Verified mapping used for conference 136 article `Гнисюк`: section 1 → `ECONOMIC THEORY, MACRO- AND REGIONAL ECONOMY`.

# Canonical ETALON style map

| Semantic role | Required style |
|---|---|
| section label | `SECTION` |
| DOI / DOI URL | `UDC` |
| УДК / UDC | `UDC` |
| human author name | `AUTOR` |
| degree, role, institution, city/country, ORCID | `pip` |
| article title | `Назва1` |
| paragraph containing image/SmartArt/shape/chart | `РИС` |
| figure caption | `РисПід` |
| every paragraph inside table cells | `TABLETEXT` |
| references heading | `REF-TITLE` |
| each reference entry | `REFER` |

Annotations/abstracts and keywords are normalized by `naukainfo-annotation-keywords-normalization` as template `Normal` paragraphs with the ordinary body first-line indent; they are not headings. Table number/title and figure/source-note handling is delegated to `naukainfo-table-figure-caption-contract`; reference heading/entries are finalized by `naukainfo-reference-block-fidelity`.

# Procedure

1. Work on a copy of ETALON.
2. Identify the article range after `TABLE OF CONTENTS` and before the protected tail section.
3. Insert the section heading from the manifest/library.
4. Classify article front matter and assign styles from the map.
5. Preserve text, run emphasis, numbering XML, hyperlinks, drawings, SmartArt relationships, merged cells and author alignment.
6. Remove conflicting direct font-size/bold overrides only when they prevent the canonical style from rendering as defined.
7. Apply `TABLETEXT` to every visible table-cell paragraph, including merged/nested cells, without flattening header alignment or emphasis.
8. Reopen the saved DOCX and assert actual style names, not visual similarity.
9. Run semantic-indent, table-fidelity, shape-fidelity and content-integrity audits.
10. Render every page and inspect section, front matter, figures, tables, references and protected tail.

Use `scripts/finalize_business_semantics.py` as the authoritative deterministic implementation; the earlier visual-approximation style script was removed.

# Stop conditions

Stop for review if the section label is not in the official library, the article title or author boundary is ambiguous, style assignment changes numbering/TOC unexpectedly, or any object/text is lost.

# Done when

The section appears once in English, every required paragraph has the exact canonical style, no protected role has a positive first-line indent, article content/object counts match the source, and rendered pages pass visual QA.


---

# FILE: skills/naukainfo-conference-intake/MODULE.md

---
name: naukainfo-conference-intake
description: Scans a conference Excel manifest and application folder, filters service documents, identifies probable articles, converts no files, and produces match candidates and readiness reports. Use for conference intake, scan-only, missing article investigation, or service-file classification.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Default mode: read-only scan

1. Call `scan_conference` with internal LLM disabled.
2. Read `scan_manifest.json`, `scan_files.json`, `scan_matches.json`, `scan_skipped_files.json`, `scan_summary.json`.
3. Verify Excel article count, probable files, matched, missing, duplicates and free listeners.
4. Service documents include applications, forms, receipts, payment confirmations and participant questionnaires. Do not classify solely by extension; inspect ambiguous DOCX content read-only.
5. Legacy `.doc` is reported as `requires_word` during scan; conversion happens only on a workspace copy during build.
6. For ambiguous candidates, activate `naukainfo-article-structure` and record explicit decisions in the decision bundle.

## Gotchas

- A multi-paragraph article title may be detected as only its first line.
- A free-listener form may contain a report title but is still not an article.
- File/folder names can be more reliable than a truncated title, but must not override Excel identity without evidence.
- Diagnostic build may intentionally continue with warnings to collect all errors; final build may not.

## Output

Use a table with Excel ID, authors, Excel title, candidate, detected title, score, decision and reason.


---

# FILE: skills/naukainfo-docx-audit/MODULE.md

---
name: naukainfo-docx-audit
description: Runs structural, text, object, Excel reconciliation, UDC/DOI, empty paragraph, section order, references numbering, table, shape/textbox, and source immutability checks on a built journal. Use after every diagnostic or full build and before finalization.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.1.0"
---

# Audit order

1. Verify source and ETALON hashes unchanged.
2. Excel vs journal reconciliation: all expected articles, no extras/duplicates.
3. Text integrity: no unexplained content loss.
4. Object integrity: tables, images, formulas, shapes/textboxes, OLE, media/embeddings.
5. Front matter: DOI/UDC/authors/title ordering and missing fields.
6. Sections/order/page starts.
7. Tables: exact source↔target text/structure, effective first-line indent through style inheritance, alignment, runs, font/spacing, cell/row geometry and rendered fit. Route mismatches to `naukainfo-table-format-fidelity`.
8. References: each article restarts at 1; no lost numbering.
9. Shape/textbox font and geometry.
10. Produce operator actions separated into critical, high, medium and low.

## Severity

Critical:
- missing article;
- text/object loss;
- corrupted/open-failing DOCX;
- ETALON/raw modification;
- broken article order;
- missing title/author that prevents identification.

Warning/manual review:
- generated UDC;
- ambiguous header line;
- table geometry not safely measurable;
- caption style variation;
- low-priority blank page from trailing empty paragraphs.

Never mark final based only on the agent’s subjective visual impression.


---

# FILE: skills/naukainfo-etalon-section-pagination-fidelity/MODULE.md

---
name: naukainfo-etalon-section-pagination-fidelity
description: Preserves the ETALON section-break graph, footer relationships, and internal page-number start so journal pagination remains identical to the template after assembly.
license: Proprietary project skill
compatibility: Word DOCX/OOXML; NAUKAINFO ETALON; Дирежор project only.
metadata:
  author: naukainfo
  version: "3.0.0"
---

# Purpose

The ETALON contains a deliberate three-section layout. The middle section carries the running footer/page field and `w:pgNumType w:start="1"`; the protected final service page is a separate section. Losing or flattening these `sectPr` nodes makes page numbers disappear or restart incorrectly.

# Contract

1. Work on a copy of ETALON and preserve its complete ordered `w:sectPr` sequence.
2. Preserve section-break positions, `footerReference`/`headerReference` relationships, `w:pgNumType`, page size, margins, columns, and title-page flags.
3. Insert the article body only into the designated middle content section; do not rebuild the document body from plain XML fragments that discard section properties.
4. Preserve the required template page break between the copyright/front matter and `TABLE OF CONTENTS`.
5. Preserve the protected final service-page section.
6. After assembly, assert the expected section count and the exact numbered section signature from ETALON.
7. Render the whole journal and verify visible internal page numbers on TOC/article pages.

# Fail closed

Stop with `ETALON_SECTION_PAGINATION_BLOCKED` when section count, footer relationships, `pgNumType`, or visible page numbers differ from ETALON. Never repair missing numbers by adding ad-hoc typed numerals.

# Worked

Preserving all three ETALON sections, including the middle `start=1` page-number section and its footer relationship.

# Removed from active logic

Replacing the article area while dropping body-level `sectPr`, or assuming a visually similar single-section document is acceptable.


---

# FILE: skills/naukainfo-etalon-slot-insertion/MODULE.md

---
name: naukainfo-etalon-slot-insertion
description: Inserts one or more validated article copies into the structural content slot of ETALON-JOURNAL.docx: after the TABLE OF CONTENTS page break and immediately before the section-break paragraph that begins the protected tail page. Preserves the template shell, page numbering, media, article objects and tail page. Use for diagnostic article-in-template tests and journal assembly.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; DOCX composition support required.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Preconditions

- Match is validated by author name and article title.
- ETALON and raw article hashes are captured.
- Work is performed on copies only.
- Requested output mode is explicit: original-authentic or normalized 11 pt/single.

# Structural slot rule

Do not use hard-coded paragraph numbers.

1. Find the paragraph whose visible text is `TABLE OF CONTENTS`.
2. Continue forward to the page-break paragraph that closes the contents page.
3. Find the next paragraph that owns `w:sectPr`; this section break begins the protected tail page.
4. Insert article body elements immediately before that section-break paragraph.

This location keeps the contents page in front, starts inserted articles on the existing next page, and leaves the protected tail page after all inserted content.

# Composition requirements

- Never overwrite `ETALON-JOURNAL.docx`.
- Merge styles, numbering, relationships and media; do not copy only plain text.
- Preserve tables, merged cells, figures, captions, drawings, hyperlinks, lists and authored page breaks.
- Remove the article-level terminal section properties when they would replace master page setup.
- Each additional article starts on a new page.
- Preserve the master document-level section settings and protected tail section.

# Two supported outputs

## Original-authentic

Insert the untouched validated article copy and preserve all authored typography.

## Minimal normalization

First apply `naukainfo-minimal-normalization`, then insert the resulting copy. Default typography is 11 pt and single line spacing while preserving emphasis and objects.

# Mandatory validation

After composition:

1. Confirm ETALON and raw hashes are unchanged.
2. Confirm all article paragraphs occur in the output in source order.
3. Confirm table and drawing counts equal template plus article counts.
4. Confirm temporary insertion markers are absent.
5. Render every page to PNG and inspect all pages.
6. Confirm article starts after TABLE OF CONTENTS and protected tail page remains last.

# Done when

Both structural and visual checks pass and the output is explicitly labeled diagnostic or production.


---

# FILE: skills/naukainfo-figure-cluster-fidelity/MODULE.md

---
name: naukainfo-figure-cluster-fidelity
description: Treats each figure, embedded caption/textbox, external caption, and source note as an atomic ordered cluster and prevents loss or detachment.
version: "2.9.0"
---
# Atomic figure cluster

Protected order signature:
`preceding prose → figure object → caption → source note → required blank → following prose`.

Audit both main body and nested `w:txbxContent`. Every drawing/picture/object paragraph uses the template figure-object style `РИС` (`styleId ad`). Every recognized caption (`Рис.`, `Мал.`, `Fig.`, `Figure`, `Abb.`, `Abbildung`, `AGD1`, etc.) uses `РисПід` (`styleId af6`), single spacing, centered, zero first-line indent.

A caption embedded inside a shape is still a caption. A composite raster containing several subfigures is one author object unless the source contains separate editable objects.

Release fails if a source object is absent, reordered, detached from its caption, clipped, outside printable margins, or replaced by a different image hash.


---

# FILE: skills/naukainfo-free-listener-toc-section/MODULE.md

---
name: naukainfo-free-listener-toc-section
description: Adds the mandatory final FREE LISTENERS section to the three-column TABLE OF CONTENTS from the verified manifest whenever free listeners exist.
license: Proprietary project skill
compatibility: NAUKAINFO manifest + ETALON TOC; Дирежор project only.
metadata:
  author: naukainfo
  version: "3.0.0"
---

# Source of truth

Free listeners come from the manifest/Excel intake, not from article DOCX files. They are non-article participants but must appear in the final TOC when present.

# Contract

1. Read the verified `LISTENERS` manifest group after article matching.
2. If the group is non-empty, append one merged section row `FREE LISTENERS` after all article sections in the same three-column TOC table.
3. Add one author row per listener using `TabTaitl` for the sequence number, `TabPIP` for the name, and a blank page-number cell.
4. Continue numbering after the final article record.
5. If a listener has an approved report note/title, add a following title row with `TabTaitl`; do not invent report titles.
6. Do not create article pages, UDC, authorship styles, or page numbers for listeners.
7. Rebuild the listener section from the final manifest on every release; never retain stale rows from an older TOC.

# Conference 136 verification

Expected: six listener records. The final listener section must include all six names and the approved report title for Olena Zorczykowska.

# Fail closed

Stop if manifest listener count differs from TOC listener count, duplicate names appear, or the section is missing when listeners exist.


---

# FILE: skills/naukainfo-front-matter-order-and-title-dedupe/MODULE.md

---
name: naukainfo-front-matter-order-and-title-dedupe
description: Normalize article front matter to UDC/DOI -> author header -> title, merge split titles, and prevent duplicated titles.
---

# Front Matter Order and Title Deduplication

## Canonical order
Every article must be transformed into this order before body processing:
1. optional DOI line;
2. UDC/УДК line;
3. author block: `AUTOR` + `pip` lines;
4. exactly one blank paragraph;
5. article title with style `Назва1`;
6. exactly one blank paragraph;
7. article body beginning with annotation/keywords or the first body paragraph.

## Non-standard source orders
The source may use:
- UDC -> title -> header;
- title -> header -> no UDC;
- UDC -> header -> title;
- split title across multiple adjacent paragraphs.

The builder must semantically identify UDC, author block, title and body, then output only the canonical order.

## Split titles
If the title is broken into multiple adjacent title-like paragraphs, merge them into one `Назва1` paragraph, preserving the exact words in their original order.

## Duplicate-title prevention
After the canonical title is emitted, the original title paragraph(s) from the source must not be copied again into the body.
Before final delivery, run a duplicate-title scan:
- for every `Назва1`, find the next non-empty paragraph;
- if it equals the title text and is not the annotation/keywords/body, delete the duplicate;
- log the deletion as a generator-regression fix.

## Spacing
- Exactly one blank paragraph must appear between the last header line and the title.
- Exactly one blank paragraph must appear after the title.
- More or fewer blank paragraphs are invalid.

## What worked
- Canonical reorder stage before body copy.
- Duplicate scan after assembly.

## What did not work and is removed from active logic
- Setting `body_start_idx` manually without excluding the original title paragraph.
- Assuming the title always appears in the same source order.


# v1.1 anti-regression rules

- Canonical frontmatter order is **DOI/UDC → author header → article title → annotation/abstract**.
- Do not insert a new title if a source title already exists; move/style the existing title instead.
- If the title was originally before the header, move it below the cleaned header and add exactly one blank paragraph before the title and one after it.
- Title dedupe must compare normalized text, including collapsed spaces and removed line breaks.
- Header cleanup must finish before TOC rebuilding, because the TOC author line is derived from `AUTOR` paragraphs.


---

# FILE: skills/naukainfo-frontmatter-supervisor-and-pip-split/MODULE.md

---
name: naukainfo-frontmatter-supervisor-and-pip-split
description: Splits author headers into person lines and metadata lines, recognizes scientific supervisors as people, prevents degrees/titles from receiving AUTOR style, and preserves all non-contact affiliation content.
version: "2.8.0"
---

# Person vs metadata

`AUTOR` is assigned only to a person or explicit participant name. Degrees, titles, positions, academies, cities, and affiliations use `pip`.

Examples of metadata that must not be `AUTOR`:

- `член-кореспондент НАМН України`;
- `доктор медичних наук, професор`;
- `здобувач`, `студент`, `аспірант`;
- affiliation, department, city, country.

# Scientific supervisors

Lines such as `Науковий керівник: доцент Тимонін Ю. О.` must be split:

- `Науковий керівник:` / `доцент` → `pip` as service role text;
- `Тимонін Ю. О.` → `AUTOR` because this is a person who participated in supervision/editing.

The rule is generic, not name-specific.

# Long lines

Long author header lines may be split for readability without deleting text. Move city/country/affiliation fragments to following `pip` paragraphs when this makes the header compact and readable.

# Contacts

Emails, phones, Telegram/Viber/WhatsApp and similar personal contacts are removed without leaving empty paragraphs. ORCID is preserved.


---

# FILE: skills/naukainfo-journal-assembly/MODULE.md

---
name: naukainfo-journal-assembly
description: Builds a NAUKAINFO draft journal from validated article copies in Excel/section order using a copy of the master template. Use after scan and matching are understood, with explicit human approval for a full build.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Preconditions

- Preflight completed.
- Raw-root and ETALON hashes captured.
- Output is an isolated workspace.
- Diagnostic or production intent is explicit.
- Build approval token is available.

## Procedure

1. Call `build_journal` with `approval="BUILD_CONFIRMED"`.
2. Default to internal LLM disabled in agent-driven mode.
3. Use only a copied template.
4. Insert only non-empty official sections. Resolve each section from the validated section library, render its heading in English only, insert it once before the first article, and apply `SECTION`.
5. Insert articles in manifest order; each article starts on a new page.
6. Preserve the template’s covers, headers, footers, numbering and protected tail pages.
7. Activate `naukainfo-canonical-style-application` for every inserted article; actual ETALON style IDs are mandatory.
8. Do not perform a global style replacement that collapses author-specific visual semantics.
8. Record all created files and the exact command.

## Diagnostic build

A diagnostic build may continue with unmatched/needs-review items only after user confirmation. It must enumerate omissions and never be labeled final.

## Done when

A draft and all expected reports exist, source/template hashes are unchanged, and the artifact list is complete.


---

# FILE: skills/naukainfo-legacy-doc-image-recovery/MODULE.md

---
name: naukainfo-legacy-doc-image-recovery
description: Recovers images omitted by legacy binary DOC conversion and blocks release until recovered media are visually matched and reinserted in source order.
version: "2.9.0"
---
# Legacy DOC recovery

A DOC→DOCX conversion is not proof that all author media survived. For binary `.doc` sources, compare source rendering, converted media parts, and OLE streams (`WordDocument`, `Data`, `0Table/1Table`).

If source rendering shows an image missing from converted DOCX:
1. Preserve the source and all prior releases unchanged.
2. Run `scripts/recover_legacy_doc_images.py` into a separate recovery folder.
3. Match recovered images visually to the source page and caption.
4. Reinsert the exact recovered bytes in original order as a stable inline object unless the original anchor can be safely preserved.
5. Apply `РИС` to the object paragraph and the caption contract to its caption.
6. Compare SHA-256, relationships, page bounds, order, and final render.

Never invent, redraw, crop, replace, or omit author media. Ambiguity is `MEDIA_FIDELITY_BLOCKED`.


---

# FILE: skills/naukainfo-manifest-evidence-matching/MODULE.md

---
name: naukainfo-manifest-evidence-matching
description: Builds an evidence-based article manifest by matching every Excel participant/article record to an exact source document using the two primary identity signals: author full name and article title. Records the source filename, extracted evidence, confidence, and unresolved conflicts. Use before normalization, styling, ordering, or journal assembly.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; DOCX/XLSX readers required.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Sources of truth

- Excel/manifest supplies expected participants, article titles, sections and ordering.
- Raw DOCX files supply author headers, titles and article content.
- Folder names and filenames are supporting clues only; they cannot replace document evidence.

# Required matching evidence

For each expected article record capture:

1. Excel row/index and expected author name(s).
2. Expected article title exactly as stored in Excel.
3. Exact source DOCX path and filename.
4. Extracted author line(s) from the DOCX.
5. Extracted article title from the DOCX.
6. Author-name match result.
7. Title match result.
8. Supporting clues, if used: folder name, filename, UDC, institution, ORCID.
9. Final status and confidence.

# Decision rule

A record is `matched` only when both primary signals agree:

- surname and given name identify the expected author or co-author;
- article title is the same after conservative normalization of case, whitespace, punctuation and line breaks.

A filename-only or folder-only match is never sufficient.

## Statuses

- `matched_exact` — author and title both agree exactly or after conservative normalization.
- `matched_reviewed` — both primary signals agree, but transliteration, initials, hyphenation or minor title punctuation required operator-reviewed normalization.
- `ambiguous` — author agrees but title conflicts, title agrees but author conflicts, or multiple source files satisfy the same record.
- `missing_source` — Excel expects an article but no qualifying source DOCX exists.
- `unregistered_source` — a DOCX appears to be an article but has no Excel record.
- `non_article` — questionnaire, receipt, certificate request or other administrative file.

# Output contract

Produce a manifest row for every expected article and a separate inventory row for every discovered DOCX. Never silently omit duplicates or unresolved files.

The report must make the reasoning auditable in plain language, for example:

`Soloviov Oleh Volodymyrovych — found in 043_9eb86041.docx because the DOCX header contains the author’s surname and given name, and the extracted title matches the Excel title after whitespace normalization.`

# Done when

- every Excel article record has a status;
- every discovered DOCX has a classification;
- exact source filenames are recorded;
- both primary signals are shown independently;
- unresolved conflicts are isolated before styling or assembly.


---

# FILE: skills/naukainfo-media-object-fidelity-gate/MODULE.md

---
name: naukainfo-media-object-fidelity-gate
description: Blocks journal assembly when any image, drawing, SmartArt, shape, textbox, nested image/table, formula, OLE object, caption, or source note from the article body is lost, reordered, detached from its caption, or rendered outside the page bounds.
version: "2.8.0"
---

# Non-negotiable gate

Article-body media is protected author content. A built journal is invalid if any article loses a drawing, image, SmartArt, grouped shape, textbox, nested table, caption, or source note.

# Root-cause lesson

A previous build lost **Figure 2** in the Magdysiuk article. Paragraph text checks passed, but the DrawingML relationship/media part was not carried through. This proves that text checks are insufficient.

# Required audit per article

Before normalization and after journal assembly, compute and compare:

- drawing/inline/anchor counts;
- `a:blip` rIds and media targets;
- VML/object/OLE/embedded package counts;
- textboxes and `w:txbxContent` blocks;
- tables nested inside textboxes/shapes;
- nearby captions: `Рис.`, `Fig.`, `Figure`, `Мал.`, `Таблиця`, `Table`;
- order signatures: text paragraph → object → caption/source note.

# Fix strategy

- Copy missing media bytes and relationships from the article source, not from a previous generated journal.
- Preserve object order and anchors where possible.
- If a missing object cannot be reattached automatically, stop with `MEDIA_FIDELITY_BLOCKED` and return the article name, source paragraph signature, and missing rId/media target.
- After repair, render and visually inspect the page containing every recovered object.

# Stop conditions

- Source has N drawings/media objects and final has fewer.
- A caption exists without its object, or object exists without its source caption.
- Object is clipped, outside margins, or extends beyond the printable page.
- Shape/textbox content is not inspected recursively.

## v2.9 extension

Counts alone are not proof. Compare relationship targets, SHA-256 hashes, dimensions, order signatures, and source-page visual evidence. For binary `.doc`, invoke the legacy recovery skill when conversion omits media.

## v3.0 source-to-final object completeness

Audit every article independently, not only the aggregate journal. A source article with two chart/figure objects must still have both in the final article region. Conference 136 regression fixtures include Magdysiuk Figure 2 and Todorova Figure 2; either missing object is a hard release blocker. Verify object order, relationship target, media hash, caption adjacency, and rendered presence.


---

# FILE: skills/naukainfo-minimal-normalization/MODULE.md

---
name: naukainfo-minimal-normalization
description: Normalizes article copies with minimal visual change: 11 pt, single spacing, table paragraphs without first-line indent, and shape/textbox text at 11 pt while preserving body order, emphasis, objects, anchors, numbering, and author intent. Use only on workspace copies after a validated plan.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.2.0"
---

# Safety first

1. Call `snapshot_inputs` before write operations.
2. Work only on a copied article in workspace.
3. Use the existing project normalizer through `prepare_conference` or the project’s specific normalizer tool; do not reimplement DOCX editing in the skill.

## Allowed default changes

- body font size 11 pt;
- single line spacing;
- table cell text 11 pt and single;
- no first-line indent in table cells; verify the effective value through style inheritance and invoke `naukainfo-table-format-fidelity` after ETALON insertion;
- shape/textbox text 11 pt and single;
- minimal table/image/caption alignment repair.

## Preserve

- paragraph order and content;
- bold/italic/underline where authored;
- structural, template, section and article-start page breaks;
- author-inserted internal page breaks by default, except pagination-helper candidates explicitly evaluated by `naukainfo-pagination-break-reflow`;
- list and reference numbering unless a specific repair is approved;
- table merges, widths and row properties unless overflow repair is needed;
- inline/floating image geometry and anchors;
- formulas, drawings, pict, embeddings and OLE.

## Validation loop

After normalization compare source vs copy:
- text tokens excluding allowed service cleanup;
- table/image/formula/shape/OLE counts;
- reference numbering;
- page/object geometry when Word rendering is available.

After 11 pt / single normalization, invoke `naukainfo-pagination-break-reflow` for manual breaks near tables because font reduction may make an old pagination helper obsolete.

After insertion into ETALON, invoke `naukainfo-semantic-style-routing` and `naukainfo-table-format-fidelity`; a target `Normal` style may add an effective indent even when the copied paragraph has no direct indent property.

Stop and report on unexplained loss.


If editable figures are detected, invoke `naukainfo-shape-object-fidelity` before and after insertion.


---

# FILE: skills/naukainfo-multi-article-assembly/MODULE.md

---
name: naukainfo-multi-article-assembly
description: Assembles multiple already-validated NAUKAINFO articles into one ETALON journal while preserving section order, article-start page breaks, objects, and independent reference numbering restarted at 1 for every article. Use after single-article style/layout QA and before final TOC materialization.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; docxcompose; NAUKAINFO Journal Builder project.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Preconditions

- Every input article has already passed canonical style, table/figure, spacing, shape and reference-block QA.
- Article order and official English section names are confirmed from the manifest/section library.
- `ETALON-JOURNAL.docx` is read-only and the output is a new workspace copy.

# Procedure

1. Extract only the article body range: first `SECTION` paragraph through the last `REFER` entry. Never append another copy of the cover, service pages or protected tail.
2. Preserve full OOXML package relationships for tables, images, SmartArt, shapes, textboxes and numbering; do not merge as plain text.
3. Insert articles in manifest order before the protected tail section. Add `pageBreakBefore` to every article/section after the first so every article starts on a new page.
4. Keep a section heading only once before the first article of each non-empty section. When consecutive articles belong to the same section, omit repeated `SECTION` paragraphs.
5. After composition, rebuild each reference block independently:
   - one fresh `w:num` instance per article;
   - `w:startOverride=1`;
   - one `numId` inside the block and a different `numId` for the next article;
   - remove copied `w:tabs`, direct `w:ind`, foreign numbering and character overrides.
6. Reopen and audit exact paragraph/table text sequence against every source article. A change in text, row/cell structure or object signature is a hard failure.
7. Render the assembled journal. Determine actual internal start pages only after pagination stabilizes, then materialize the static TABLE OF CONTENTS.
8. Re-render all pages. Confirm that the protected final service page is last and that no extra blank page was created by appended section properties.

# Mandatory gates

- Each reference block visibly starts with `1.` and structurally uses a distinct `numId` with start override 1.
- Every article starts on a new page.
- Exact source text/table sequence is unchanged.
- SmartArt/diagram relationship parts and source media hashes are preserved.
- Only `SECTION`, `AUTOR` and `Назва1` have TOC outline levels.
- No appended body-level or paragraph-level section artifacts create a blank trailing page.

# What worked

- Trimming styled single-article ETALON copies to the semantic article range before composition.
- `docxcompose` for relationship/media import, followed by targeted section-artifact cleanup.
- Fresh numbering instances after the final merge, not before it.
- Two-pass TOC: render first, then insert actual start pages and render again.

# What did not work and must not be reused

- Appending complete single-article journals, which duplicates covers and tail pages.
- Trusting source `numId` values after composition; they may be remapped or continue across articles.
- Generating TOC page numbers before final pagination.
- Accepting object counts without exact text/table signatures and full-page visual QA.

# Done when

The merged DOCX passes structural/content/style/reference audits and every rendered page is inspected at 100% zoom.

## v2.1 addition: static TOC page numbers
When building a multi-article draft, insert the static table of contents at the existing `TABLE OF CONTENTS` location, render the DOCX to PDF/PNG, locate actual article start pages, then update TOC page numbers and render again. Internal page number = physical PDF page minus the unnumbered front matter offset. For current NAUKAINFO journal shell, the offset is 2.

The final TOC must include section heading, article number + author(s), article title, and verified starting page.


---

# FILE: skills/naukainfo-multilingual-marker-library/MODULE.md

---
name: naukainfo-multilingual-marker-library
description: Provides conservative multilingual recognition for figure/table captions and reference headings without rewriting article prose.
version: "2.9.0"
---
# Marker library

Use `scripts/normalize_multilingual_markers.py` as the shared classifier.

Supported examples:
- figures: `Рис.`, `Рисунок`, `Мал.`, `Fig.`, `Figure`, `Abb.`, `Abbildung`, `Rys.`, `Obr.`, `AGD1`;
- tables: `Таблиця`, `Table`, `Tabelle`, `Tabela`, `Tabulka`, `Tableau`, with or without a number;
- references: Ukrainian source/literature variants, English `References/Bibliography`, German `Literaturverzeichnis/Quellenverzeichnis`, and common Polish/Czech/Slovak/French variants.

Strip a leading section number only for marker classification, e.g. `14. Список використаних джерел`. Do not alter ordinary prose that merely contains these words.

Canonical output follows article language: Ukrainian stamp for Ukrainian articles, `REFERENCES` for English, standard German distinction for German articles.


---

# FILE: skills/naukainfo-numbering-definition-fidelity/MODULE.md

---
name: naukainfo-numbering-definition-fidelity
description: Preserve author list numbering/bullets when assembling NAUKAINFO journals from multiple DOCX articles.
---

# NAUKAINFO Numbering Definition Fidelity

## Scope
Only for the Дирежор / NAUKAINFO Journal Builder project and only after explicit activation in the current project chat.

## Priority
This skill is subordinate to `naukainfo-author-body-fidelity` and supports it: author body lists must not silently change visual type, numbering scheme, bullet symbol, indentation, list level, or restart behavior.

## Business rule
When a paragraph in the author body has `w:numPr`, the final journal must preserve both:

1. the paragraph `numId/ilvl` relationship, and
2. the referenced `numbering.xml` definitions (`abstractNum`, `num`, `numFmt`, `lvlText`, paragraph indent, tabs, run font for bullets).

It is not enough to preserve the paragraph XML. If a multi-document merge remaps `numId` to an existing decimal list, a source bullet list can visually become `1.` / `2.`. This is a critical body-fidelity failure.

## Allowed exceptions
References are handled by `naukainfo-reference-block-fidelity` and must be rebuilt as independent decimal lists starting at 1 for each article. This exception applies only after the canonical heading `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`.

## Required algorithm

1. Before article insertion, snapshot every source paragraph with `w:numPr`:
   - source article id / file;
   - paragraph text hash;
   - role: body list or reference entry;
   - `numId`, `ilvl`;
   - resolved `abstractNumId`;
   - `numFmt` and `lvlText` for that `ilvl`;
   - paragraph indentation and tab settings;
   - bullet run font if any.
2. During insertion, never reuse a destination `numId` unless its resolved definition is semantically identical.
3. If the destination already has that `numId`, allocate a fresh `numId` and copy the source `abstractNum`/`num` pair.
4. After assembly, audit every non-reference list paragraph against its source snapshot.
5. Stop the build if a body bullet became decimal or a decimal list became bullet.
6. Render and visually inspect the affected page.

## Regression example fixed in v2.7
In the Hnysiuk article, two body paragraphs beginning:

- `Пряма форма включає заробітну плату...`
- `Непряма матеріальна мотивація спрямована...`

were source bullet paragraphs (`numFmt=bullet`, `lvlText=-`) but after merging their `numId=41` pointed to a decimal abstract definition, rendering as `1.` and `2.`. The correct fix is to preserve/copy the source bullet numbering definition. No author text may be changed.

## Verification gate
A final DOCX passes only when:

- all body list paragraphs keep their original list kind and marker;
- all reference lists restart independently at 1;
- no manual body list is converted into references;
- render confirms the visible markers.


---

# FILE: skills/naukainfo-pagebreak-and-empty-paragraph-policy/MODULE.md

---
name: naukainfo-pagebreak-and-empty-paragraph-policy
description: Removes author-inserted page breaks and stray empty paragraphs inside articles while preserving required journal spacing and ensuring each article starts on a new page.
version: "2.8.0"
---

# Page breaks

Author manual page breaks inside an article are not accepted. Remove them unless they are the journal assembly boundary between articles.

During journal assembly, every article must start with a real page break / section-aware boundary before DOI/UDC, not with an accidental empty paragraph.

# Empty paragraphs preserved by business rules

Keep or create exactly one empty paragraph:

- after UDC/UDC line;
- between the cleaned author header and the article title;
- after article title;
- after annotation/abstract only when required by business layout;
- after keywords;
- after each table, figure, or `Джерело:` / `Source:` note;
- before and after the reference heading stamp.

# Empty paragraphs removed

Remove stray author blank paragraphs before ordinary body paragraphs, before numbered body paragraphs, and around manual page breaks if they are not one of the allowed business spacing points.

# Safety

Removing an empty paragraph must never remove adjacent text or join two articles. If deleting a blank before UDC causes article merge, insert/restore the article page break instead.

## v3.0 article-boundary and spacing contract

- Do not create an empty paragraph that contains only a manual page break before an article.
- Remove author-inserted page breaks from inside article bodies.
- Set `pageBreakBefore` on the first structural paragraph of every article (`SECTION` when newly emitted, otherwise DOI/UDC). This creates a clean new-page start without a dummy paragraph.
- Preserve the ETALON front-matter page break before `TABLE OF CONTENTS`; it is outside the article region and is not an author break.
- There must be no blank paragraph between `Анотація`/`Abstract` and `Ключові слова`/`Keywords`.
- There must be exactly one blank paragraph after the keywords block.
- There must be exactly one blank paragraph immediately before a table/figure cluster when the preceding paragraph is ordinary body text, and one after the complete cluster/source note.


---

# FILE: skills/naukainfo-pagination-break-reflow/MODULE.md

---
name: naukainfo-pagination-break-reflow
description: Re-evaluates author-inserted manual page breaks after font-size and spacing normalization, especially around tables. Removes only obsolete pagination-helper breaks after rendered comparison confirms acceptable publication aesthetics and table continuity; preserves structural and article-start breaks.
license: Proprietary project skill
compatibility: Windows 11; Microsoft Word rendering recommended; Python 3.11+; NAUKAINFO Journal Builder project.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

Authors may insert a manual page break while preparing an article at 14 pt so that a table starts or continues cleanly. After normalization to 11 pt and single spacing, that break may create an unnecessary blank area or force a table onto a new page even though the preceding page now has enough space. Re-evaluate such breaks only after normalization and only on a workspace copy.

## Hard boundaries

Never remove:

- the page break that starts a new article;
- ETALON/template structural breaks;
- section breaks or paragraph-level `w:sectPr`;
- breaks required to protect cover, contents, service, or tail pages;
- a break whose purpose cannot be identified confidently.

Treat only author-inserted pagination-helper page breaks near tables, captions, or table-introducing paragraphs as candidates.

## Candidate detection

Inspect explicit `w:br w:type="page"`, `pageBreakBefore`, and equivalent Word pagination properties:

1. immediately before a table or its caption;
2. between consecutive parts of one logical table;
3. in the short paragraph sequence after a table-introducing sentence;
4. where the source at a larger font size shows a table-preservation intent.

Record the exact paragraph/table position and the evidence for classifying it as a candidate.

## Required comparison

Create two temporary copies after 11 pt / single normalization:

- **A — preserved break**;
- **B — candidate break removed**.

Render both with Word-compatible pagination. Do not decide from OOXML text flow alone when rendering is available.

## Removal criteria

Remove the candidate only when all conditions are satisfied:

1. no text, table row, image, formula, caption, footnote, or object is lost, clipped, overlapped, or reordered;
2. the result looks suitable for a published proceedings volume and does not create an excessive blank zone;
3. the table either:
   - fits wholly on one page; or
   - splits across pages in a balanced way no rougher than approximately **60/40** by table volume;
4. the caption/number and table header are not orphaned from the table body;
5. repeated header rows, merged cells, row non-splitting settings, and notes under the table remain correct;
6. the following page does not begin with only a tiny residual fragment of the table.

A 60/40 threshold means the smaller page fragment should represent about 40% or more of the table and the larger fragment about 60% or less. A more balanced 50/50 split is acceptable. A 70/30, 80/20, single-row, or similarly abrupt split is not acceptable by default.

## Measuring the split

Preferred metric: rendered vertical height occupied by the table on each page.

Fallback when reliable rendered geometry is unavailable:

- use weighted row height rather than raw row count;
- include merged-row span and fixed row heights;
- exclude caption and source note from table-volume percentage, but evaluate them separately for orphaning.

If the metric is uncertain or close to the threshold, preserve the break and mark `needs_operator_review`.

## Decision outcomes

- `remove_obsolete_break`: all criteria pass;
- `preserve_break`: removal damages layout or creates an unbalanced table split;
- `needs_operator_review`: intent or rendered result is ambiguous.

## Audit trail

For every evaluated break record:

- article ID, author, and title;
- source file and normalized copy;
- OOXML location/type of break;
- reason the break was considered author-inserted;
- table identifier and page numbers in variants A and B;
- split ratio or “fits whole page” result;
- before/after screenshots or rendered PDF pages;
- final decision and confidence.

## Done when

The chosen copy passes text/object integrity checks, pagination rendering, and visual regression review, with every removed break explained in the audit report.


---

# FILE: skills/naukainfo-preflight/MODULE.md

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


---

# FILE: skills/naukainfo-project-context/MODULE.md

---
name: naukainfo-project-context
description: Reads NAUKAINFO architecture, project_memory, conventions, known bugs, prior decisions, tests, and existing modules before any code or journal operation. Use at the start of every Journal Builder task, code change, audit, or production run.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

Load only the project-specific facts needed for the current task and prevent repeated mistakes.

## Procedure

1. Call `read_project_context` with the project root.
2. Read, when present: architecture, LLM policy, project conventions, decisions, known bugs, failed attempts, working solutions, regression tests and TODO.
3. Search the repository for an existing implementation before proposing new code.
4. Produce a compact context packet:
   - immutable inputs;
   - allowed changes;
   - relevant existing modules;
   - known regressions;
   - tests that protect this area.
5. Do not begin write operations until contradictions are resolved.

## Gotchas

- The new minimal-authenticity concept differs from old aggressive style normalization.
- `ETALON-JOURNAL.docx` is a master shell, never an output target.
- Some legacy code may exist after an early `return`; do not assume search results are active execution paths.
- Project memory is a contract: only supported files should be updated.

## Done when

The agent can state which existing code it will reuse and which files are protected.


---

# FILE: skills/naukainfo-project-memory/MODULE.md

---
name: naukainfo-project-memory
description: Updates NAUKAINFO project_memory after a run with verified working solutions, failures, known bugs, visual differences, regression tests, decisions, changelog, and exact artifact paths. Use after every meaningful test, build, repair, or audit.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Procedure

1. Read the memory contract before writing.
2. Record only evidence from completed runs.
3. Update the smallest relevant files:
   - `working_solutions.md` — confirmed working behavior;
   - `failed_attempts.md` — failed approaches and root causes;
   - `known_bugs.md` — reproducible unresolved issues;
   - `regression_tests.md` — tests/fixtures/commands and results;
   - `visual_differences.md` — observed permitted/unintended differences;
   - `decisions.md` — architectural choices and rejected alternatives;
   - `changelog.md` — concise change entry;
   - `todo.md` — next actions.
4. Include run ID, command, input conference, report paths and test results.
5. Do not write unsupported filenames and do not overwrite prior history.

## Quality

Separate fact from inference. Never record “validated” unless a test or audit actually ran.


---

# FILE: skills/naukainfo-project-scope-guard/MODULE.md

---
name: naukainfo-project-scope-guard
description: Prevents NAUKAINFO/Dирежор skills from leaking into unrelated chats or projects.
license: Proprietary project skill
metadata:
  version: "1.0.0"
---

# Rule

Use NAUKAINFO Agent Skills only inside the Дирежор / NAUKAINFO Journal Builder project and only after explicit activation in the current chat or clearly in-scope journal-builder work.

# Default behavior outside scope

Do not load, cite, apply, update, or infer from these skills. Follow only platform defaults and the instructions in that separate chat.

# Forbidden

- No automatic use in general Word/Excel/PDF tasks.
- No changing these skills from another project.
- No replacing another chat's formatting rules with NAUKAINFO styles.


---

# FILE: skills/naukainfo-quality-gate/MODULE.md

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


---

# FILE: skills/naukainfo-reference-block-fidelity/MODULE.md

---
name: naukainfo-reference-block-fidelity
description: Normalizes each article's references block to the NAUKAINFO stamp, exact ETALON REF-TITLE/REFER styles, fresh per-article numbering, and correct hanging-indent geometry. Use after article insertion and before pagination/TOC generation.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; NAUKAINFO ETALON numbering; Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "2.0.0"
---

# Purpose

A paragraph can show style `REFER` yet still render incorrectly because copied direct indentation, tabs or a foreign `numId` override the ETALON definition. This skill makes the references block structurally correct, not merely visually similar.

# Canonical stamp

For Ukrainian articles the heading is exactly:

`СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`

Do not use `СПИСОК ВИКОРИСТАНОЇ ЛІТЕРАТУРИ`, `ЛІТЕРАТУРА`, or author-specific variants.

# Spacing contract

1. Exactly one empty paragraph before the stamp.
2. Exactly one empty paragraph between the stamp and reference entry 1.
3. Stamp uses actual style `REF-TITLE`, centered, bold as defined by ETALON, 11 pt, single, first-line indent 0, and keep-with-next.
4. No positive first-line indent is allowed in the stamp.

# Reference-entry contract

1. Every entry uses actual style `REFER`.
2. Each article has a fresh numbering instance restarted at 1; do not reuse a foreign/source `numId` or continue numbering from another article.
3. Remove direct `w:ind` and direct tab stops that override the style/numbering geometry.
4. The ETALON numbering definition supplies decimal `%1.` with left/hanging geometry of 567 twips (approximately 1 cm).
5. Entries are 11 pt, single, justified, with 0 pt before/after.
6. Continuation lines align on the text line, not under the numeral; no bullet glyphs or arrow/tab artifacts may appear.
7. Preserve reference text and language, but clear imported character formatting equivalent to `Ctrl+Space`; hyperlink underline/color, shading and foreign character styles are not preserved.
8. Reconstruct manual numbering and Enter-split continuation paragraphs through `naukainfo-reference-entry-reconstruction`.
9. Prefix ordinary web links with `URL: ` and DOI URLs/bare DOI identifiers with `DOI: `.

# Procedure

1. Detect the article references boundary before the protected tail/article break.
2. Replace the heading text with the canonical stamp.
3. Normalize surrounding blank paragraphs.
4. Create a fresh numbering instance based on the verified ETALON reference abstract numbering definition and restart it at 1.
5. Apply `REFER`, remove conflicting direct indents/tabs/foreign numbering, and attach the fresh `numId`.
6. Reopen and assert heading/style/blank spacing/numbering/direct-indent invariants.
7. Render all reference pages and visually compare the hanging alignment with a published NAUKAINFO PDF/template.

Use `scripts/finalize_business_semantics.py` as the authoritative finalizer. `normalize_captions_references.py` remains only as a lower-level compatibility utility and is not the acceptance gate.

# Stop conditions

Stop if entries cannot be reliably separated, the template reference numbering definition is missing, or the source contains mixed bibliography subsections requiring editorial judgment.

# Done when

The canonical stamp is present once, spacing is exact, numbering restarts at 1, every entry is `REFER`, no conflicting direct indent remains, and rendered continuation lines align correctly.

## v3.0 unmarked terminal bibliography inference

When an author omits a heading such as `Література`/`References`, inspect the terminal article block conservatively. Infer a references block only when all strong signals hold: it is at the end of the article; it contains at least two consecutive citation-like entries or one citation-like entry with clear bibliographic/URL/DOI evidence; numbering is manual or automatic; and the block is separated from the final body/conclusion. Insert the language-appropriate canonical stamp and apply fresh `REFER` numbering from 1. If evidence is ambiguous, stop for operator review rather than reclassifying body text.


---

# FILE: skills/naukainfo-reference-entry-reconstruction/MODULE.md

---
name: naukainfo-reference-entry-reconstruction
description: Reconstructs logical bibliography entries when authors typed numbers manually, used Enter inside one citation, mixed manual/automatic numbering, or pasted formatted hyperlinks. Use before canonical REFER numbering and reference-block fidelity.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; OOXML/python-docx; NAUKAINFO Jurnal.dotx.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Why

A source bibliography may display `1., 2., 3.` but the digits can be typed characters rather than Word numbering. An author may press Enter inside one citation, producing continuation paragraphs that would otherwise become false new entries. The final list must preserve citation text while becoming a clean Word list.

# Boundary detection

Treat a paragraph as a new entry when at least one reliable signal exists:

- Word `numPr` automatic numbering;
- a leading manually typed number such as `1.`, `1)`, `(1)`;
- an already validated `REFER` paragraph.

An unnumbered paragraph following a detected entry is a continuation and is joined to the previous entry with one space. Remove the redundant paragraph. If no reliable boundaries exist for a multi-paragraph bibliography, stop with `REFERENCE_BOUNDARIES_AMBIGUOUS` for operator review; never merge everything silently.

# Cleanup equivalent to Ctrl+Space

After reconstruction, rebuild the complete entry as plain template text before assigning `REFER`:

- remove imported character styles, shading, highlighting, underlining and hyperlink blue;
- remove foreign direct tabs/indents and source `numId`;
- retain the exact textual content;
- assign a fresh per-article numbering instance with `startOverride=1`.

# URL and DOI labels

- Every ordinary `http://` or `https://` link must be immediately preceded by `URL: `.
- A DOI URL (`https://doi.org/...` or `http://dx.doi.org/...`) and a bare DOI identifier (`10.xxxx/...`) must be immediately preceded by `DOI: `.
- Normalize duplicated or wrong labels (`URL: DOI:`, `URL: https://doi.org/...`) to the correct single label.
- A DOI label is valid and is not replaced with URL.

# QA

- Compare reconstructed entry count and concatenated citation text with source evidence.
- Check each article’s first visible reference number is 1 and that `numId` is distinct between articles.
- Assert no manual leading numeral remains in entry text.
- Assert all web/DOI strings have the correct label.
- Render every reference page and inspect hanging alignment.

Implemented in `scripts/finalize_business_semantics.py`.


---

# FILE: skills/naukainfo-reference-language-and-marker-contract/MODULE.md

---
name: naukainfo-reference-language-and-marker-contract
description: Recognizes Ukrainian and English reference headings, replaces them with the correct language-specific stamp, and applies REFER numbering independently per article.
version: "2.8.0"
---

# Ukrainian articles

Use exactly:

`СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`

# English articles

Use exactly:

`REFERENCES`

Do not replace an English article’s references block with the Ukrainian stamp.

# Recognition

Recognize variants such as:

- `Список використаних джерел`, `Список літератури`, `Література`, `References`, `Reference list`, `Bibliography`;
- numbered headings such as `14. Список використаних джерел` or `References:`.

Normalize the heading, then apply the correct `REF-TITLE` and rebuild entries with `REFER`, restarting from 1 for each article.

# DOI/URL in references

- ordinary web links must be preceded by `URL:`;
- DOI links or DOI strings must be preceded by `DOI:`;
- preserve the rest of the reference text.

## v2.9 multilingual extension

Use the shared marker library. German `Literaturverzeichnis` and `Quellenverzeichnis` are separate standard headings; preserve that distinction. Recognize numbered markers such as `14. Список використаних джерел`, remove only the service number, and rebuild the list from 1. English `REFERENCE.` normalizes to `REFERENCES`.


---

# FILE: skills/naukainfo-semantic-style-routing/MODULE.md

---
name: naukainfo-semantic-style-routing
description: Classifies article paragraphs by semantic role, preserves Normal body indentation for prose/annotation/keywords, and applies zero positive first-line indent only to service metadata, author/title/object/table/list/reference roles while preserving numbering, hanging indents, and source fidelity.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; NAUKAINFO ETALON styles; Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "2.0.0"
---

# Purpose

`ETALON-JOURNAL.docx` defines a 1 cm first-line indent in `Normal`. Paragraphs copied from an article can silently inherit that indent even when the original has none. This skill identifies paragraph roles before final assembly and prevents the template body indent from leaking into service and object-related text.

# Canonical semantic roles

## No positive first-line indent

The following roles must have an effective first-line indent of zero:

- DOI and DOI URL;
- `УДК` / `UDC`;
- author names, scientific degrees, positions, institutions, city/country and ORCID lines;
- article title;
- paragraphs that contain an image, SmartArt, shape group, chart or other drawing object;
- figure captions and figure source notes;
- table number, table title, table source/note;
- every paragraph inside every table cell, including nested tables;
- bulleted and numbered list items: the marker/list geometry is preserved, but a positive body-style first-line indent is forbidden;
- reference-list heading;
- reference entries: no positive first-line indent; an intentional hanging indent for numbering is allowed and must be preserved.

## Normal body paragraphs

Ordinary article body paragraphs, annotation/abstract paragraphs and keywords paragraphs use the authoritative `Normal` style and its ordinary first-line indent. The annotation/keywords labels are normalized separately by `naukainfo-annotation-keywords-normalization`. Do not remove body indentation globally. Section and author/title formatting follows the exact template style nodes.

# ETALON style map

After article insertion, assign the existing template styles structurally. Visual similarity without the correct style ID is a regression. Use the styles below after their side effects are validated:

| Semantic role | Canonical style | Rule |
|---|---|---|
| section name | `SECTION` | once before the first article of a section |
| UDC/УДК | `UDC` | left, bold, zero first-line |
| author name | `AUTOR` | preferred mapping; verify outline/TOC behavior |
| author details | `pip` | preferred mapping; verify outline/TOC behavior |
| article title | `Назва1` | centered title/TOC source |
| figure object paragraph | `РИС` | centered, zero first-line |
| figure caption | `РисПід` | use only if its bold/center formatting matches the publication contract |
| table cell paragraph | `TABLETEXT` | zero first-line; never flatten header alignment |
| reference heading | `REF-TITLE` | centered, bold, uppercase |
| reference entry | `REFER` | preserve numbering and hanging geometry |

A style name is not enough. After assignment resolve effective formatting, reopen the DOCX, and render. If a style changes alignment, numbering, outline level, TOC membership or emphasis beyond the contract, keep the source style and apply a narrow direct zero-indent override instead.

# Deterministic procedure

1. Work on a workspace copy.
2. Detect the article content range between `TABLE OF CONTENTS` and the protected tail section.
3. Classify paragraphs with exact signals: DOI/UDC prefixes, article-title structure, annotation/keyword prefixes, drawing XML, `Рис.`/`Figure`, `Таблиця`/`Table`, source-note prefixes, list numbering XML, and reference-heading markers.
4. Apply a direct zero first-line override only to protected roles; never apply it to annotation/abstract or keywords.
5. Preserve `w:numPr`, list markers and hanging indents. If a reference already has `w:hanging`, do not add a conflicting `w:firstLine`.
6. Apply zero first-line to every table-cell paragraph recursively.
7. Reopen and audit after save.
8. Render every page and inspect all figure, table, list and reference pages.

Use `scripts/semantic_paragraph_roles.py` for the deterministic classification, repair and JSON audit.

# Stop conditions

Stop for operator review when:

- article boundaries or title cannot be identified reliably;
- a style assignment would change TOC/outline behavior unexpectedly;
- a paragraph may be either body text or a caption/reference;
- reference numbering or list markers change;
- drawings/tables move, clip or split poorly after the repair;
- any protected role retains a positive effective first-line indent.

# Done when

All protected roles have zero effective first-line indent, prose/annotation/keywords keep the intended Normal indent, list/reference numbering is stable, tables and drawings are unchanged, and the full render passes visual QA.


---

# FILE: skills/naukainfo-shape-object-fidelity/MODULE.md

---
name: naukainfo-shape-object-fidelity
description: Preserves SmartArt, grouped shapes, text boxes, DrawingML/VML fallback content, embedded text, relationship parts, extents, anchors, and visual layout when an article is normalized and inserted into ETALON. Use whenever a DOCX contains editable figures with text rather than only raster images.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; lxml; python-docx; Microsoft Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

Editable figures with text are not ordinary images. SmartArt and grouped Word shapes can depend on multiple OOXML parts and relationships. A naive body copy may preserve the visible placeholder but lose the diagram drawing part, text, geometry or fallback representation.

# Detection

Before normalization or insertion, inspect the DOCX package for:

- `dgm:relIds` and `word/diagrams/data*.xml`;
- `word/diagrams/drawing*.xml` and diagram drawing relationships;
- `w:txbxContent` in DrawingML or VML shapes;
- grouped shapes, anchors/inlines and extents;
- fallback `mc:AlternateContent` branches;
- charts, OLE and embedded objects near the same paragraph.

# Source-of-truth checks

For every SmartArt/shape object compare source and target:

- ordered text signature inside shapes;
- object count and type;
- data-model and drawing relationship validity;
- drawing part bytes/XML where exact preservation is expected;
- extent (`cx`, `cy`), anchor/inline mode and position;
- text-box paragraph/run order and text;
- font size after the allowed 11 pt normalization;
- rendered visual arrangement, connectors, borders and text wrapping.

# Safe transfer procedure

1. Copy the source article and normalize ordinary paragraphs/tables.
2. Patch text inside `w:txbxContent` and DrawingML/SmartArt runs to 11 pt without rasterizing the object.
3. Insert article body into a copy of ETALON.
4. Audit SmartArt relationships by exact text signature.
5. If the target data model exists but its `diagramDrawing` relationship/part is missing, copy the verified source drawing part, add a new relationship and content-type override, and patch the target `dataModelExt` relationship id.
6. Refuse automatic repair when a drawing part has dependent relationships that are not copied deterministically.
7. Reopen, audit and render all pages.

Use:

- `scripts/normalize_11_with_shapes.py` for 11 pt normalization inside text boxes/SmartArt;
- `scripts/shape_object_fidelity.py` for relationship and content fidelity auditing/repair.

# Verified case

The skill was validated on article `136/Заявки/27 Гнисюк/Гнисюк_тези.docx`, which contains a SmartArt-style motivation diagram with four text blocks. The source and ETALON copy retained the exact text signature, extent and drawing XML after repair and rendered correctly.

# Stop conditions

- missing or ambiguous source object;
- unmatched text signatures;
- dependent drawing relationships;
- lost text-box content;
- geometry drift, clipping, overlap or connector loss;
- any rasterization not explicitly approved.

# Done when

All editable figure objects remain editable, their text and relationships match the source, 11 pt normalization is applied where authorized, and every rendered page passes visual inspection.


---

# FILE: skills/naukainfo-shape-textbox-nested-table-contract/MODULE.md

---
name: naukainfo-shape-textbox-nested-table-contract
description: Recursively inspects DrawingML/VML shapes, textboxes, grouped objects, and nested tables so captions and table text inside shapes receive journal styles and do not overflow the page.
version: "2.8.0"
---

# Problem covered

Some authors insert what visually looks like a picture, but technically it is a shape/textbox/group containing a table and captions. In Matviienko-style articles, captions such as `РИС. 1. СХЕМА АРХІТЕКТУРИ МОДЕЛІ` may live inside `w:txbxContent`, and tables inside those shapes can inherit wrong spacing or first-line indent.

# Required recursion

Every shape audit must inspect:

- `w:drawing`, `wp:inline`, `wp:anchor`;
- `wps:txbx`, `v:textbox`, `w:txbxContent`;
- grouped shapes and nested paragraphs;
- `w:tbl` elements inside shapes/textboxes;
- captions and source notes inside shapes.

# Formatting rules inside shapes

- Figure captions inside shapes get `РисПід`/caption-equivalent formatting: 11 pt, single spacing, centered, no first-line indent.
- Table captions inside shapes follow the table-caption contract.
- Table cell paragraphs inside shapes get no first-line indent and single spacing.
- Shape/table width must be constrained to the printable area; no element may extend beyond page margins.

# Rendering gate

Render the page containing the nested shape at 100% zoom. The build fails if the shape/table overflows, clips, or loses text.

## v2.9 style routing

All drawing/object paragraphs, including containers with nested tables, receive `РИС`; all recognized captions inside or outside the container receive `РисПід`. Nested table paragraphs must have single spacing and zero first-line indent.

## v3.0 deep-container style assertion

The audit must assert both container and nested roles. The outer object paragraph receives `РИС`; every caption paragraph inside `w:txbxContent`/DrawingML/VML receives `РисПід` when it is a figure caption. Nested table labels/titles follow the canonical table-label/title split, and nested cell paragraphs receive single spacing with zero first-line indent. Compatibility-fallback duplicates in DrawingML/VML must be formatted consistently without deleting either branch.


---

# FILE: skills/naukainfo-skill-map-change-log/MODULE.md

---
name: naukainfo-skill-map-change-log
description: Records verified skill changes, successful and failed approaches, active sequence, regression evidence, and short user-facing release notes.
version: "2.9.0"
---

# naukainfo-skill-map-change-log

## Purpose
Keep the Agent Skills library operational, ordered, and non-redundant during NAUKAINFO Journal Builder work.

## Mandatory sequence
After each confirmed correction or regression:
1. Name the affected skill(s).
2. Record what worked.
3. Record what failed.
4. Remove failed approaches from active decision logic.
5. Update the skill map and changelog.
6. Add/adjust deterministic tests when the rule is stable.
7. Return a short user-facing skill report.

## Active rule
Do not keep obsolete logic merely because it once worked visually. Visual similarity is not enough; style IDs, outline levels, numbering IDs, object preservation, and text fidelity must be verified.


---

# FILE: skills/naukainfo-spacing-toc-contract/MODULE.md

---
name: naukainfo-spacing-toc-contract
description: Enforces NAUKAINFO blank-line spacing around article titles, figures, tables, source notes, and reference blocks, and guarantees only section, author names, and article titles enter the TOC outline.
---

# NAUKAINFO spacing + TOC contract

Use after semantic styling and before final render.

## Blank-line rules

- Insert exactly one empty paragraph after each article title (`Назва1`) before the annotation or body text.
- Insert exactly one empty paragraph after a figure caption (`РисПід`) when there is no separate source note below it.
- If a figure/table has a source note (`Джерело:` / `Source:`), treat the source note as the closing part of that figure/table block and insert exactly one empty paragraph after the source note.
- Insert exactly one empty paragraph after every table block. If the table has a source note, the empty paragraph goes after the source note, not between the table and the source note.
- Insert exactly one empty paragraph before and after the canonical reference stamp `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`.

## TOC/outline contract

Only these roles may have outline levels for automatic TOC generation:

1. section heading: `SECTION`;
2. author full name: `AUTOR`;
3. article title: `Назва1`.

Author metadata (`pip`), DOI/UDC, annotations, keywords, figure/table captions, source notes, table text, references, and ordinary body text must not have outline levels, heading styles, or inherited heading behavior.

## Regression rule

If a previous method only made the page visually similar but left `pip` or ordinary text as a heading/outline item, remove that method from the pipeline and replace it with structural OOXML style/outline checks.


---

# FILE: skills/naukainfo-table-caption-split-contract/MODULE.md

---
name: naukainfo-table-caption-split-contract
description: Normalizes table captions written as a single author line into the NAUKAINFO two-line table caption format without changing the caption meaning.
version: "2.8.0"
---

# Canonical format

If an author writes:

`Таблиця 1 – Порівняння підходів до обробки запитів`

or similar one-line variants, convert to:

1. `Таблиця 1` — separate paragraph, bold, right aligned.
2. `Порівняння підходів до обробки запитів` — next paragraph, centered, caption style/`РисПід`-equivalent, single spacing.

The dash/colon after the number is formatting noise and may be removed only if the title text is preserved exactly.

# Constraints

- Do not rewrite the title.
- Do not delete table context.
- Keep the caption with the table.
- Apply this both in body text and inside shape/textbox `w:txbxContent`.

## v3.0 canonical inline-caption split

For an author line such as `Таблиця 1 – Порівняння підходів до обробки запитів`, preserve both semantic parts but remove only the separator dash: create `Таблиця 1` as a separate bold right-aligned paragraph, then the title as a separate centered bold caption paragraph (template caption style where compatible). Keep the table immediately after the title and prevent the label/title from splitting away from it.


---

# FILE: skills/naukainfo-table-figure-caption-contract/MODULE.md

---
name: naukainfo-table-figure-caption-contract
description: Applies and audits the verified NAUKAINFO publication contract for table numbers, table titles, table-cell text, source notes, drawing paragraphs and figure captions after an article is inserted into ETALON. Use before pagination and visual QA.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; NAUKAINFO ETALON styles; Word or LibreOffice rendering.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

Prevent author formatting, copied direct properties, or ETALON style inheritance from producing inconsistent table/figure captions or first-line indents.

# Verified contract

## Tables

1. Table number is a separate paragraph above the title: `Таблиця N` / `Table N`.
2. The number is right aligned, bold, 11 pt, single, first-line indent 0, spacing before/after 0, and kept with the next paragraph.
3. The table title is the next non-empty paragraph, centered, bold, 11 pt, single, first-line indent 0, spacing before/after 0, and kept with the table.
4. Every paragraph inside every table cell uses actual ETALON style `TABLETEXT`.
5. Preserve author cell alignment, bold/italic emphasis, merged cells, widths, row heights, vertical alignment and repeating headers.
6. No table-cell paragraph may inherit a positive first-line indent from `Normal`.
7. A source/note below the table is 11 pt, single, first-line indent 0; preserve author italic and alignment unless the project explicitly normalizes it.

## Figures / SmartArt / shapes

1. The paragraph containing the object uses actual style `РИС`, centered, first-line indent 0.
2. The caption is below the object and uses actual style `РисПід`, centered, 11 pt, single, first-line indent 0.
3. Caption form is `Рис. N. Назва` unless the source language requires `Figure N. ...`.
4. Source/note below the caption has first-line indent 0 and preserves author emphasis.
5. Preserve anchors, wrap, size, DrawingML/SmartArt relationships and editability.

# Procedure

1. Detect table-number, table-title, figure-object, figure-caption and source-note paragraphs semantically.
2. Apply actual ETALON styles where verified; use controlled direct formatting for table number/title because ETALON currently has no dedicated canonical styles for them.
3. Remove only conflicting direct paragraph indents/spacing; do not flatten content or run emphasis.
4. Reopen the saved DOCX and audit actual style IDs and effective indentation.
5. Render every page containing a table or figure at 100% and inspect captions, splits, clipping and object geometry.

Use `scripts/finalize_business_semantics.py` as the authoritative finalizer. `normalize_captions_references.py` remains only as a lower-level compatibility utility and is not the acceptance gate.

# Stop conditions

Stop for operator review if a caption boundary is ambiguous, a table title is not adjacent to its table, a figure caption is embedded in a text box, or a layout change causes a table split rougher than the project 60/40 rule.

# Done when

All table/figure semantic roles follow this contract, objects and cell structure are unchanged, and rendered pages match publication expectations.


---

# FILE: skills/naukainfo-table-format-fidelity/MODULE.md

---
name: naukainfo-table-format-fidelity
description: Preserves table text placement when articles are normalized or inserted into ETALON. Compares source and target table paragraphs using effective style inheritance, removes unintended first-line indents introduced by the template, and verifies alignment, spacing, runs, cells, rows, merges, widths, and rendered pagination.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; Microsoft Word or LibreOffice rendering; NAUKAINFO Journal Builder project.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Purpose

A copied table may look different even when its paragraph XML has no direct indent. The target template can define a non-zero first-line indent in `Normal`, and table paragraphs that use `Normal` silently inherit it. Therefore direct-property checks alone are insufficient.

Use this skill after normalization and after insertion into `ETALON-JOURNAL.docx`, before final visual approval.

# Source of truth

1. The original article is the primary reference for table text placement.
2. The project default is no first-line indent inside table cells.
3. A deliberate non-zero source indent is preserved only when clearly authored and operator-approved.
4. Never repair the issue by globally changing the ETALON `Normal` style, because that would alter body paragraphs and service pages.

# Required checks for every table

Compare source and target by table index and cell coordinates:

- table count, row count, column count and merged-cell structure;
- exact cell text and paragraph count;
- effective first-line indent, including paragraph style and base-style inheritance;
- left/right indent, alignment, line spacing and before/after spacing;
- bold, italic, underline, font size and run order;
- cell vertical alignment and margins;
- table width, column widths, row height, row splitting and repeating headers;
- captions, notes/sources and page placement;
- rendered table split and absence of clipping or overlap.

# Effective-format rule

Do not treat `paragraph_format.first_line_indent is None` as proof that there is no indent.

Resolve the effective value in this order:

1. direct paragraph property;
2. paragraph style;
3. base-style chain;
4. document default.

When the source effective first-line indent is zero and the target inherits a non-zero indent, add an explicit direct zero override (`w:firstLine="0"`) to the target table paragraph.

# Safe repair procedure

1. Work on a workspace copy.
2. Run `scripts/table_format_fidelity.py` with source, target and output paths.
3. Refuse automatic repair if table count or structure differs materially.
4. Apply only the missing direct indent override; do not rewrite text or reconstruct tables.
5. Re-open the saved DOCX and repeat the structural comparison.
6. Require zero unexplained table-paragraph differences.
7. Render the entire document and inspect every page, with special attention to all pages containing tables and captions.
8. If font reduction changed page breaks, route separately to `naukainfo-pagination-break-reflow`.

# Audit trail

Record:

- source and target filenames;
- table/row/cell/paragraph coordinates;
- source and target effective indent with inheritance source;
- exact repair applied;
- remaining differences after save/re-open;
- table page numbers in the rendered document;
- final result: `pass`, `needs_operator_review`, or `fail`.

# Stop conditions

Stop and request operator review when:

- source and target table structure differ;
- merged cells cannot be mapped reliably;
- cell text differs;
- an indentation change appears intentional in the source;
- the repair creates clipping, a poor split, or a caption/table orphan;
- any other table typography or placement difference remains unexplained.

# Done when

All table text, paragraph/run formatting and placement match the source except explicitly approved normalization, effective first-line indent is correct, and the rendered document passes visual review.


---

# FILE: skills/naukainfo-toc-author-cleaning/MODULE.md

---
name: naukainfo-toc-author-cleaning
description: Clean author display names for the Table of Contents without leaking roles, institutions, degrees, ORCID, cities, contacts, or supervisor lines.
---

# TOC Author Cleaning

This skill is invoked after article front matter is normalized and before `naukainfo-toc-table-builder` materializes the static table of contents.

## Rule

TOC author cells must contain **only participant names**, separated by commas. They must not include:

- degrees, titles, ranks, professional positions;
- institution or department names;
- city/country lines;
- ORCID, e-mail, phone, messenger or other contact data;
- words like `науковий керівник`, `PhD`, `Senior Lecturer`, `Department`, `University`, `імені`, unless these words are part of a person's actual name, which is exceptional and requires review.

## Source of truth

1. Prefer cleaned author names from the manifest/evidence-matching layer.
2. If the manifest is incomplete, parse only the source article header **before the title** and accept a paragraph as an author candidate only if it matches a person-name pattern.
3. When a source line combines name + role/degree, split for TOC display; preserve the original line in the body unless header-normalization has an explicit safe rule to split it.
4. Never build TOC author text by simply joining every paragraph styled `AUTOR`: body style errors must not leak into the table of contents.

## Person-name acceptance

Accepted examples:

- `Соловйов Олег Володимирович`
- `Косинський П. І.`
- `Novak Natalya`
- `Sherbon Fedir`

Rejected examples:

- `PhD in Architektur`
- `Senior Lecturer of Acting`
- `імені Івана Огієнка`
- `Bohdan Khmelnytskyi National Academy of`
- `м. Одеса, Україна`
- `https://orcid.org/...`

## QA

Fail the TOC author gate if any TOC author cell contains role/institution/contact tokens or if a known article participant is missing. Store the cleaned author map in the QA report.

## Regression fixed in v2.4

The 24-article release exposed a defect where scanning raw `AUTOR` paragraphs pulled role and institution lines into the TOC. The active fix is: **TOC author display uses a cleaned author map; `AUTOR` is a signal, not a source by itself.**


---

# FILE: skills/naukainfo-toc-body-author-sync/MODULE.md

---
name: naukainfo-toc-body-author-sync
description: Rebuilds TOC author rows from final AUTOR paragraphs after header cleanup and fails on stale, missing, duplicated, or role-only author entries.
version: "2.9.0"
---
# TOC/body synchronization

The TOC is rebuilt only after all final `AUTOR`/`pip` decisions. Its author row must exactly equal the ordered `AUTOR` paragraphs between UDC and title for that article.

Never reuse stale author text from an earlier TOC. Degrees and roles such as `Hon. PhD` or `член-кореспондент...` must not appear in the TOC. Scientific supervisors marked as participating people do appear as `AUTOR`.

Run `scripts/audit_toc_author_sync.py` after the final TOC rebuild. Any missing coauthor, extra role, duplicate, or title mismatch blocks release.


---

# FILE: skills/naukainfo-toc-table-builder/MODULE.md

---
name: naukainfo-toc-table-builder
description: Build NAUKAINFO TABLE OF CONTENTS as a real three-column Word table using canonical Tab_* styles, the PDF-proven row geometry, and post-render page numbers.
---

# NAUKAINFO TOC Table Builder

## Priority
High. The table of contents must be generated from the actual styled article body, not typed manually as loose paragraphs.

## Source of truth
Use the ETALON/Jurnal styles and compare the visual result with previously published NAUKAINFO PDFs. The verified PDF pattern is:

- `TABLE OF CONTENTS` title centered above the table;
- each section is a centered bold all-caps row;
- each article has a separate narrow number column, a wide author/title column, and a right page-number column;
- the author line is bold italic;
- the article title is on the next row in all caps;
- page number is aligned right on the author row.

## Canonical table geometry
1. Locate the placeholder/title paragraph `TABLE OF CONTENTS` in the ETALON/Jurnal template.
2. Delete all old TOC body content between `TABLE OF CONTENTS` and the first real article `SECTION` paragraph.
3. Insert one real Word table with exactly three physical columns.
4. Use fixed grid widths close to the PDF layout: narrow number column, wide content column, narrow right page column. Current working grid: `[600, 8300, 739]` twips.
5. Keep borders invisible/no borders.
6. Insert section rows as one merged row spanning all 3 columns. Do **not** repeat the section text separately in each cell.
7. For every article insert exactly two rows:
   - row A: column 1 = `N.`, column 2 = author(s), column 3 = verified page number;
   - row B: column 1 = blank, column 2 = article title, column 3 = blank.
8. Never put the title in the same row as the author. This was the v2.2 defect that made the content column too narrow and visually unlike the PDF.

## Required styles
Use the actual style IDs from the template, not guessed names:

| TOC role | Visible style name | OOXML styleId |
|---|---|---|
| section row | `Tab_SEC` | `TabSEC` |
| author cell | `Tab_PIP` | `TabPIP` |
| article title cell | `Tab_Taitl` | `TabTaitl` |
| article number cell | `Tab_Taitl` | `TabTaitl` |
| page number cell | `Tab_Taitl` + direct right alignment | `TabTaitl` |

## TOC record collection
1. Group records by the nearest preceding `SECTION` paragraph.
2. Collect author rows only from `AUTOR`.
3. Collect title only from `Назва1` / styleId `11` in the verified Word 2010 template.
4. Do not use `pip`, UDC, DOI, annotations, captions, references, table text or body paragraphs for TOC rows.
5. Deduplicate author names within one article and duplicate titles caused by front-matter reconstruction.

## Pagination workflow
1. Assemble the journal body first.
2. Render the document and determine actual internal article start pages.
3. Build or update the static TOC with final page numbers.
4. Render again and inspect the TOC page visually against a known PDF.
5. No `?` placeholders may remain.

## Failure modes that stop the build
- TOC is made of loose paragraphs instead of a 3-column table.
- Section text appears repeated in three cells instead of one merged section row.
- Article title appears in the same row as the author.
- A `pip` line enters the TOC.
- Any article has no `AUTOR` or no `Назва1`.
- Page numbers are stale after pagination changed.
- The TOC is visually narrower/wider than the PDF reference after render.

## What worked
- PDF-based reconstruction: section merged row + two article rows.
- Using `TabSEC`, `TabPIP`, `TabTaitl` style IDs directly from the template.
- Wide middle column so Ukrainian long titles wrap like the published PDF.

## What did not work and is removed from active logic
- v2.2 one-row article layout: `[number+author] [title] [page]`.
- Three equal-width columns.
- Repeating section text in all three cells.
- Loose paragraph TOC generation.
- Manual page numbers before final render.


## v2.4 full-release page and author rules

- Do not detect article start pages by the first occurrence of an article title in the rendered PDF: the title also appears inside the TOC. Page detection must exclude TOC page occurrences by starting after the TOC block/body-start page or by requiring article-front-matter evidence such as UDC/DOI near the title.
- TOC author text must be supplied by `naukainfo-toc-author-cleaning`; never concatenate all `AUTOR` paragraphs without filtering.
- If a same-section block contains multiple articles, the section row is printed once, while each article still receives its own page break.

## v2.9 final-source rule

Never retain author rows from an earlier TOC. After final `AUTOR`/`pip` classification, rebuild the complete TOC table from body styles and then run `audit_toc_author_sync.py`.

## v3.0 free-listener tail section

After all article sections, invoke `naukainfo-free-listener-toc-section`. When the manifest contains free listeners, append the merged `FREE LISTENERS` row and all verified listener names to the same three-column table. Listener rows have no article page numbers and do not create body articles.


---

# FILE: skills/naukainfo-udc-review/MODULE.md

---
name: naukainfo-udc-review
description: Detects a missing UDC, prepares a compact online classification request from title/abstract/keywords/section, requires evidence and operator approval, inserts the approved code with the canonical UDC style, and enforces exactly one blank paragraph after it.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; online-capable LLM/agent; NAUKAINFO Jurnal.dotx; MCP tools recommended.
metadata:
  author: naukainfo
  version: "2.0.0"
---

# Hard gate

- If `УДК ...` / `UDC ...` is present, preserve it. Never replace an author-supplied code automatically.
- If it is absent, the build must stop with `UDC_LOOKUP_REQUIRED`; do not silently omit UDC or invent a code offline.

# Online lookup workflow

1. Collect only the article title, annotation/abstract, keywords and validated official section. Add a short body excerpt only if the topic remains ambiguous.
2. Send that compact classification packet to an online-capable LLM/agent and require web research against authoritative/current UDC catalogues, library classifications or highly relevant indexed publications.
3. Return one primary candidate and up to three alternatives with:
   - exact `УДК ...` or `UDC ...` string;
   - topic reasoning;
   - evidence URLs/source names;
   - confidence;
   - `needs_operator_review: true`.
4. Store the proposal in `agent_decisions.json` and do not insert it until operator approval.
5. After approval, insert the UDC immediately after any DOI service line and before the author block.
6. Apply the exact authoritative template style `UDC`.
7. Insert **exactly one empty Normal paragraph after the UDC**—not zero and not more than one.

# Validation

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


---

# FILE: skills/naukainfo-unnumbered-table-label-contract/MODULE.md

---
name: naukainfo-unnumbered-table-label-contract
description: Recognizes a standalone table marker even when the author omitted the table number and applies canonical table-label formatting without inventing a number.
version: "2.9.0"
---
# Unnumbered table labels

A standalone `Таблиця`, `Table`, `Tabelle`, or equivalent directly associated with a table is a valid table label even without a number.

Apply: Times New Roman 11 pt, bold, right aligned, single spacing, zero first-line indent, keep with next. Preserve the absence of a number; never invent `1` merely because there is one table.

The next caption/title paragraph is centered and preserved verbatim. If label and title share one line (`Таблиця 1 – Назва`), use the table-caption split contract and remove only the separator dash/colon, not title content.


---

# FILE: skills/naukainfo-versioned-backup-release/MODULE.md

---
name: naukainfo-versioned-backup-release
description: Preserves immutable versioned backups of source documents, prior journal releases, skills packages, and QA reports before every repair or rebuild.
version: "2.9.0"
---
# Versioned backups

Never overwrite the source article, ETALON, prior release, prior skills ZIP, or prior QA report. Every repair produces a new versioned filename and records its parent input.

Minimum retained chain:
- source/original article archive;
- last accepted journal release;
- current stage and final release;
- previous and current skills archives;
- QA reports and recovery artifacts.

A cleanup may remove caches, temporary renders, and failed disposable stages only after the new release passes QA. Versioned backups are not deleted automatically.


---

# FILE: skills/naukainfo-visual-regression/MODULE.md

---
name: naukainfo-visual-regression
description: Renders a built DOCX through Microsoft Word to PDF/page images and compares layout, blank pages, tables, images, shapes, captions, and page boundaries against source/reference artifacts. Use when visual authenticity matters or after any DOCX layout change.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.1.0"
---

# Requirements

Windows with Microsoft Word. Work on output copies only.

## Procedure

1. Call `render_docx_pdf` for the draft.
2. Record page count and detect blank pages.
3. Compare article boundary pages, pages containing tables, figures, shapes/textboxes and reference blocks. For tables, verify the first text line starts at the same horizontal position as in the source and that no style-inherited indent appears.
4. When a baseline exists, compare page images and produce a difference report.
5. Distinguish permitted differences (11 pt/single) from unintended movement, clipping, lost objects or numbering changes.

## Gotchas

- Object counts alone do not prove geometry preservation.
- A blank page from trailing empty paragraphs + an inter-article break is low/medium priority unless it affects pagination/TOC materially.
- Complex merged tables may not expose stable column widths through COM; require a visual checkpoint.
- Do not use OCR as the primary comparison when Word/PDF text extraction is available.
