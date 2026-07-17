---
name: journal
description: Єдиний проєктний скіл для повного циклу NAUKAINFO Journal Builder у проєкті «Дирежор»: приймання матеріалів, підготовка статей, збирання журналу в ETALON, збереження авторського тексту/форматування/об'єктів, зміст, нумерація сторінок, рендер, published-reference parity, глибокий аудит і реліз.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; lxml; LibreOffice; NAUKAINFO Journal Builder.
metadata:
  author: naukainfo
  version: "3.3.0"
  priority: "0-critical"
  scope: "Дирежор / NAUKAINFO Journal Builder only"
---

# ЖУРНАЛ — єдиний головний скіл

## Активація і межі

Цей скіл працює лише коли:

1. поточний проєкт — «Дирежор» / NAUKAINFO Journal Builder;
2. користувач явно активував скіл «журнал» або доручив збирання/перевірку журналу;
3. завдання стосується цього журналу.

В інших проєктах не застосовувати ETALON, стилі, TOC або бізнес-правила цього пакета.

## Абсолютний пріоритет

Авторське тіло статті є джерелом істини. Без явного дозволу заборонено:

- переписувати, скорочувати, доповнювати, переставляти або перекладати текст;
- змінювати кількість авторів;
- втрачати абзаци, слова, таблиці, рисунки, формули, shapes, SmartArt, text boxes, підписи, примітки чи джерела;
- змінювати ручні списки на автоматичні або навпаки, крім окремо дозволеної реконструкції references;
- знімати авторське bold/italic/underline, індекси або вирівнювання підзаголовків;
- приймати «візуально схоже» або однакову кількість об'єктів як доказ цілісності.

Дозволені лише затверджені службові правки: UDC/УДК, очищення шапки від контактів, AUTOR/pip, назва, стандартні мітки annotation/keywords/references, канонічні підписи, службові blanks, розриви та стилі без зміни змісту.

## Двоцільова модель якості

1. **Hard constraint:** нуль непогоджених текстових або об'єктних втрат.
2. **Optimization target:** серед безпечних варіантів мінімізувати структурно-верстальну відстань до реально опублікованого корпусу NAUKAINFO.

Fidelity має пріоритет над parity. Published parity не дозволяє переписувати автора.

## Нульовий gate: обов'язкові активи

До будь-якої генерації знайти й перевірити:

- `02_TEMPLATES_REQUIRED/ETALON-JOURNAL.docx`;
- `02_TEMPLATES_REQUIRED/Jurnal.dotx`;
- цей `skills/journal/SKILL.md`;
- `03_REFERENCE_RELEASES/JOURNAL_136_FINAL_RELEASE_v33.docx` як regression source, не як publication truth;
- опубліковані `Conference136.pdf` і `Conference137.pdf` як layout/publication references;
- `05_TESTS_QA_AND_SCHEMAS/FILE_MANIFEST.json`;
- вхідний архів/папку статей;
- `publication_manifest.json`.

Якщо ETALON, DOTX, journal skill, article manifest або publication manifest відсутні/невалідні:

`BUILD BLOCKED: REQUIRED_ASSET_MISSING`

Не створювати master shell приблизно або з пам'яті.

Перевірити ETALON:

- рівно 3 `w:sectPr`;
- друга секція має `w:pgNumType w:start="1"`;
- footer relationship основного тексту існує;
- наявні canonical style IDs.

## Publication manifest — єдине джерело службових даних

`publication_manifest.json` обов'язково містить:

- `conference_number`;
- `conference_title`;
- `date_range`;
- `city`;
- `country`;
- `conference_url`;
- `conference_doi`;
- `isbn`;
- `approval_date`;
- `bibliographic_page_count`;
- `recommended_citation`;
- `final_service_page_text`.

Заборонено брати ці дані з тексту ETALON або попереднього релізу. ETALON дає геометрію/стилі, manifest дає факти.

### Placeholder gate

Реліз блокується при наявності в front matter або tail:

- `0000000`;
- `assignment pending`;
- `Author. Article title`;
- порожнього ISBN/DOI/page count;
- чернеткових дат або generic citation.

### Stale-template fingerprint gate

Сканувати front matter і tail на інші conference IDs, DOI, titles, dates, cities, countries, ISBN і approval dates. Будь-який токен чужої конференції = `BLOCKED`.

## Обкладинка та ілюстрації в parity-оцінці

За явним редакторським правилом для корпусу 136/137:

- перша сторінка/обкладинка не входить у style-parity score;
- піксельний вигляд авторських ілюстрацій не входить у style-parity score.

Однак fidelity-gates все одно захищають:

- наявність і порядок object cluster;
- media bytes/hash, якщо доступні;
- anchor/inline, extent, crop;
- підпис і source note;
- вплив object cluster на потік і пагінацію.

Ігнорувати вигляд зображення не означає дозволити його втрату або переміщення.

## Єдиний конвеєр

### 0. Бекап

- Не перезаписувати оригінали, ETALON, попередній release або skills ZIP.
- Для кожної статті створити immutable source manifest із hash.
- Для кожного production run створити versioned workspace.

### 1. Глибокий source snapshot

До змін зберегти:

- видимий текст у порядку документа, включно з tables і `w:txbxContent`;
- paragraphs, runs, emphasis, indices, alignment;
- manual/automatic lists і numbering definitions;
- table cells, merges, widths, order, formatting;
- images/media relationships, extents, crop, anchor/inline, order;
- shapes, SmartArt, charts, equations, OLE, captions, source notes;
- section/page-break signature;
- semantic author-header line signature.

### 2. Підготовка статті

Застосувати лише підтверджені правила:

- DOI/UDC → author/PIP block → blank → title → blank → body;
- email/phone/messenger видаляються лише з шапки; ORCID зберігається;
- annotation/abstract і keywords labels нормалізуються без зміни тексту;
- table/figure/caption/source blocks не мають first-line indent;
- nested content обробляється recursively;
- legacy `.doc` спочатку render/convert/audit.

### PIP segmentation gate

Заборонено автоматично зливати в один paragraph:

- degree/title;
- role/position;
- institution;
- city/country;
- supervisor name;
- supervisor degree/role.

Якщо ці рядки окремі у source або manifest, вони окремі у final. Порівнювати semantic line signature `source → normalized → final`.

### Reference-label preservation gate

- Existing `URL:` і `DOI:` labels зберігати.
- Не змінювати `URL:` на `DOI:` лише тому, що адреса містить `doi.org`.
- Відсутню мітку можна додати за canonical rule.
- Semantic reclassification дозволена тільки через explicit editorial decision bundle.

### 3. Вставка в ETALON

- ETALON є master shell.
- Зберегти sections, footer, page fields, front/tail pages.
- Статті й sections ідуть лише в manifest order.
- Article boundary реалізується canonical `pageBreakBefore`, без dummy blank paragraph.
- Author body не переписується для ущільнення сторінок.

### 4. Per-article audit

Для кожної статті порівнювати `raw source → normalized article → final region`:

1. lexical diff;
2. paragraph count/order;
3. run formatting;
4. list semantics;
5. tables;
6. objects/media/order;
7. nested content;
8. author count;
9. PIP semantic line signature;
10. article start page.

Unknown diff = `BLOCKED`.

### 5. TOC

TOC створюється лише після стабілізації тіла.

Кожна manifest article має рівно один row із:

- canonical English section;
- global ordinal (`1.`, `2.`, ...);
- authors only;
- comma + space як canonical author separator;
- title;
- rendered start page.

У TOC заборонені:

- degrees, roles, institutions, city/country;
- DOI/UDC;
- annotation/body text;
- semicolon як автоматичний separator;
- missing ordinal або page.

Після матеріалізації TOC виконати повторний render і повторно визначити page starts. Якщо сторінки змінилися — перебудувати TOC до convergence або блокувати run.

### 6. Per-article pagination gate

Зберігати `article_start_page_vector.json`.

- Для реконструкції 136/137 вектор має точно відповідати published PDF.
- Для нових конференцій використовувати corpus profile для anomaly detection: blank pages, detached captions, collapsed PIP, надмірні пусті зони, несподівані article-length outliers.
- Загальна кількість сторінок не замінює per-article vector.

### 7. Published-reference parity gate

Побудувати reference profile з опублікованих 136/137 після виключення cover та image pixels.

Порівнювати:

- front-matter text і paragraph geometry;
- section heading placement;
- DOI/UDC/author/title/annotation sequence;
- PIP paragraph segmentation;
- paragraph spacing, indents, line density;
- table/caption/source-note geometry;
- TOC structure;
- article start-page vector;
- tail isolation;
- last numbered page і bibliographic page count.

Parity report має розділяти:

- hard fidelity failures;
- publication metadata failures;
- layout deviations;
- intentional exceptions.

### 8. Tail isolation gate

Фінальна службова сторінка:

- починається з нової сторінки;
- перебуває в захищеній останній секції;
- не приєднана до references;
- не має page number основного тіла;
- повністю відповідає `final_service_page_text` і publication manifest.

Будь-який tail paragraph у region останньої статті = `BLOCKED`.

### 9. Render gate

Після кожної значущої серії змін:

1. render DOCX → PDF/PNG;
2. переглянути кожну сторінку при 100%;
3. перевірити tables, clipping, captions, page numbers, section transitions, blank pages;
4. після TOC/page updates — повторний render;
5. окремо перевірити front matter без cover і standalone tail.

## Фінальний fail-closed gate

`PASS` можливий лише коли:

- всі articles mapped;
- unapproved text changes = 0;
- missing paragraphs/tables/objects/captions/formulas = 0;
- author count mismatches = 0;
- run-emphasis mismatches = 0;
- numbering-definition mismatches = 0;
- PIP merged semantic lines = 0;
- stale-template tokens = 0;
- placeholders = 0;
- publication metadata mismatches = 0;
- missing/duplicate TOC rows = 0;
- TOC ordinal/page mismatches = 0;
- tail isolation failures = 0;
- unknown reference-label changes = 0;
- ETALON section/page-number signature preserved;
- published-reference parity reviewed;
- full render review passed.

Якщо будь-який пункт не доведений, статус `REVIEW` або `BLOCKED`, але не `PASS`.

## Обов'язкові артефакти релізу

- final journal DOCX;
- final rendered PDF;
- publication manifest JSON;
- final QA JSON;
- per-article text/run/table/object audits;
- PIP segmentation report;
- TOC row audit;
- article start-page vector;
- published-reference parity JSON;
- tail isolation report;
- render evidence summary;
- versioned skills ZIP + changelog.

## Done when

Реліз доведено на рівні кожної статті та всієї publication shell: нуль непогоджених втрат, нуль stale metadata/placeholders, повний TOC з точними сторінками, правильна semantic segmentation шапки, ізольована фінальна сторінка і внутрішня верстка, максимально наближена до опублікованого корпусу 136/137 без зміни авторського змісту.
