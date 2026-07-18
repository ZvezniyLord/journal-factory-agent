# План розробки Journal Builder

## Мета

Побудувати універсальну програму:

```text
RAW + manifest + ETALON + DOTX + metadata
→ prepared articles
→ journal DOCX
→ journal PDF
→ QA reports
```

Опубліковані PDF використовуються лише як golden references для тестування.

## Стек

- Python 3.11+ — orchestration, parsing, rules, CLI і QA;
- lxml — OpenXML merge;
- python-docx — безпечні високорівневі операції;
- LibreOffice або Word — рендер і field update;
- SQLite FTS5 — база маркерів, прізвищ та установ;
- JSON/JSONL — manifests, decisions і reports;
- локальна LLM — лише структурована порада для неоднозначних випадків.

## Архітектурні фази

1. **Ingest:** безпечне розпакування, SHA-256, inventory, source snapshots.
2. **Discovery:** відокремлення статей від анкет, квитанцій та службових файлів.
3. **Manifest:** порядок секцій, статей і авторів; no missing/no duplicate gate.
4. **Header parser:** DOI, UDC, автори, установи, ORCID, назва, межа body.
5. **Article preparation:** тільки дозволена нормалізація шапки без зміни body.
6. **OpenXML merge:** перенесення paragraphs, tables, drawings, equations, footnotes, media і relationships.
7. **ETALON assembly:** front matter, sections, articles, final service page.
8. **TOC/pagination:** render-measure-update loop до стабілізації сторінок.
9. **Render:** DOCX→PDF, font substitution та repair checks.
10. **QA:** source→prepared→final text/object parity, article order, TOC і visual regression.
11. **Final gate:** fail closed; PASS лише за повного набору доказів.

## Conference 95

- 95.0: assets, SHA, inventory, baseline.
- 95.1: підготовка кількох різних статей і 100% body parity.
- 95.2: таблиці, рисунки, формули, footnotes, numbering.
- 95.3: повне body assembly у правильному порядку.
- 95.4: ETALON, front matter, styles і stale-template scan.
- 95.5: TOC, рендер і pagination convergence.
- 95.6: publication parity проти official Conference95.pdf.
- 95.7: чистий повторний build для reproducibility.

## Наступні конференції

Для кожної конференції 96→135:

1. запустити незмінний ruleset;
2. зафіксувати failure class;
3. спочатку додати тест;
4. виправити загальне правило;
5. повторити поточну конференцію;
6. повторити всі попередні regression-тести;
7. зробити зрозумілий український commit;
8. оновити status і matrix.

## Другий повний прохід

Після першого проходу ruleset заморожується. Усі доступні конференції 95→135 збираються повторно з чистих workspace без conference-specific patches. Це перевіряє універсальність і виявляє overfitting.

## LLM

LLM отримує лише обмежений фрагмент шапки, кандидатів із бази та JSON schema. Вона не редагує DOCX/XML, не змінює body і не встановлює PASS. Python перевіряє відповідь і виконує тільки дозволені операції.

## Definition of Done

- body text parity = 100%;
- object loss = 0;
- кожна стаття включена рівно один раз;
- правильний порядок секцій і статей;
- DOCX відкривається без repair;
- PDF стабільно рендериться;
- TOC і printed pages правильні;
- немає `if conference_id == ...` у production rules;
- база знань має provenance;
- перший і другий corpus-проходи завершені.
