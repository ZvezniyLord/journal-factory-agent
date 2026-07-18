# Паралельна робота над конференціями

## Гілки

- інтеграція: `agent/journal-builder-integration`;
- Conference 95 і core builder: `agent/journal-builder-95`;
- конференційний агент: `agent/conference-<NNN>-fixtures`;
- база знань: `agent/core-knowledge-base`;
- рендер і QA: `agent/core-render-qa`.

## Правило власності

Щоб чати не переписували роботу один одного:

- `journal_factory/production_pipeline.py` та assembly-модулі змінює integrator;
- conference agent переважно додає fixtures, reports, observations і тести;
- knowledge agent змінює `knowledge_base/` та відповідні importer/search модулі;
- QA agent змінює render/fidelity/regression modules;
- спільний core change оформлюється окремим PR.

## Рекомендований розподіл

- головний чат: Conference 95 + core assembly;
- паралельний чат 1: Conference 96 fixtures і host observations;
- паралельний чат 2: Conference 97 fixtures і host observations;
- паралельний чат 3: knowledge base та marker extraction;
- паралельний чат 4: render, TOC, pagination і visual QA.

Поки Conference 95 не створив перший працездатний builder, інші conference agents не пишуть власні збирачі. Вони готують дані, fixtures, manifests і failure observations для того самого core.

## Контракт conference agent

Conference agent повинен залишити:

```text
fixtures/conferences/<NNN>/
reports/conferences/<NNN>/
knowledge_base/imports/conference_<NNN>.jsonl
```

Обов’язкові результати:

- source inventory;
- список кандидатів статей;
- порядок секцій і статей;
- observed header markers;
- таблиці/рисунки/формули/footnotes cases;
- expected official PDF metadata;
- host render report;
- blockers;
- proposed general rules з позитивними та негативними прикладами.

## Merge protocol

1. Оновити свою гілку від integration.
2. Запустити локальні тести.
3. Запустити regression на доступних попередніх конференціях.
4. Оновити `PROJECT_STATUS.md` лише у своєму PR section або status artifact.
5. Зробити український commit.
6. Відкрити draft PR до `agent/journal-builder-integration`.
7. Integrator перевіряє відсутність conference-specific code.
8. Після merge integrator запускає повну regression-матрицю.

## Конфлікти

Агент не вирішує конфлікт шляхом видалення чужого коду. Він:

- оновлює гілку;
- переносить тільки власні fixtures/reports;
- описує core conflict у PR;
- залишає остаточне рішення integrator.

## Паралельність без overfitting

Кожна конференція є незалежним тестом одного builder. Конференційні branches не створюють окремі production rulesets. Нове правило приймається лише коли:

- має evidence;
- не змінює авторський body;
- має regression-тест;
- проходить усі раніше прийняті конференції;
- не містить перевірки конкретного номера конференції.
