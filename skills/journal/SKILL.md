---
name: journal
description: Єдиний проєктний скіл для повного циклу NAUKAINFO Journal Builder у проєкті «Дирежор»: приймання матеріалів, підготовка статей, збирання журналу в ETALON, збереження авторського тексту/форматування/об'єктів, зміст, нумерація сторінок, рендер, body-parity з опублікованими журналами, глибокий аудит і реліз.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; lxml; LibreOffice; NAUKAINFO Journal Builder.
metadata:
  author: naukainfo
  version: "3.3.1"
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

Дозволені лише затверджені службові правки: UDC/УДК, очищення шапки від контактів, нормалізація PIP, назва, стандартні мітки annotation/keywords/references, канонічні підписи, службові blanks, розриви та стилі без зміни змісту.

## Двоцільова модель якості

1. **Hard constraint:** нуль непогоджених текстових або об'єктних втрат.
2. **Optimization target:** серед безпечних варіантів мінімізувати структурно-верстальну відстань саме до **внутрішнього змісту** реально опублікованих журналів NAUKAINFO.

Fidelity має пріоритет над parity. Published parity не дозволяє переписувати автора.

## Межі published-body parity

Для референсів Conference 136/137:

- обкладинка, титульно-службові сторінки до `TABLE OF CONTENTS` і фінальна рекламно-службова сторінка **не входять** до body-parity score;
- порівняння починається з `TABLE OF CONTENTS` і охоплює всі статті до завершення останнього списку джерел;
- піксельний вигляд рисунків не оцінюється;
- наявність, порядок, розмір, підпис і вплив рисунка/таблиці на потік та пагінацію контролюються;
- ETALON є сирою геометрично-стильовою заготовкою, а не джерелом істини для змісту чи пунктуації.

## Нульовий gate: обов'язкові активи

До будь-якої генерації знайти й перевірити:

- `02_TEMPLATES_REQUIRED/ETALON-JOURNAL.docx`;
- `02_TEMPLATES_REQUIRED/Jurnal.dotx`;
- цей `skills/journal/SKILL.md`;
- опубліковані `Conference136.pdf` і `Conference137.pdf` як body-layout references;
- `05_TESTS_QA_AND_SCHEMAS/FILE_MANIFEST.json`;
- вхідний архів/папку статей;
- article/participant manifest із порядком секцій, статей та авторів.

Якщо ETALON, DOTX, journal skill або article manifest відсутні/невалідні:

`BUILD BLOCKED: REQUIRED_ASSET_MISSING`

Не створювати master shell приблизно або з пам'яті.

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
- semantic author-header signature;
- reference-block numbering signature.

### 2. Підготовка статті

Канонічний порядок внутрішньої статті:

`SECTION → optional DOI → UDC/УДК → author/PIP block → optional ORCID → title → annotation/body`

Застосувати лише підтверджені правила:

- email/phone/messenger видаляються лише з шапки; ORCID зберігається;
- annotation/abstract і keywords labels нормалізуються без зміни тексту;
- table/figure/caption/source blocks не мають first-line indent;
- nested content обробляється recursively;
- legacy `.doc` спочатку render/convert/audit;
- не вставляти порожні абзаци для керування відступом: використовувати paragraph spacing.

### 3. Author-header composition gate

Шапка не нормалізується механічним правилом «кожне поле в один рядок» або «все об'єднати комами». Потрібна семантична композиція, як в опублікованому корпусі.

Обов'язкові правила:

- кожен автор починається окремим абзацом;
- не можна зливати кінець одного авторського блоку з наступним автором;
- degree/title, role, department, institution і location можуть складатися з одного або кількох абзаців залежно від довжини й синтаксичної цілісності;
- короткі пов'язані фрагменти можна об'єднати лише якщо так зберігається граматика й published profile;
- довгі institution/department chains переносити по природних синтаксичних межах, а не посеред назви;
- порядок semantic tokens має збігатися `source → normalized → final`;
- авторський блок у журнальному тілі має канонічне праве вирівнювання, як у 136/137;
- section heading і title мають зберігати published alignment/weight/spacing profile.

Golden fixtures для regression tests:

- 136: Гнисюк / Сімкова — supervisor chain із продовжувальними комами;
- 136: Матвієнко / Бобиль — кафедра й факультет як окремі продовжувальні рядки;
- 137: Живко та співавтори — п'ять незалежних author blocks;
- 137: Злакоман — degree, `Independent Researcher`, location, ORCID окремими рядками;
- 137: Маєр — компактне об'єднання ролі з короткою назвою ЗДО та природні переноси адміністративної назви;
- 137: Александрова — qualification/department/institution/location без злиття в один довгий рядок.

### 4. Header punctuation gate

Пунктуація в шапці є частиною верстальної логіки.

- ім'я автора — без кінцевої коми або крапки;
- location (`м. Київ, Україна`, `Kyiv, Ukraine`) — без кінцевої коми/крапки;
- рядок отримує кінцеву кому лише коли синтаксичний metadata chain продовжується в наступному рядку;
- останній рядок degree/role chain — без зайвої кінцевої коми;
- не видаляти внутрішні коми у ступенях і посадах;
- не додавати крапку з комою між авторами в шапці або TOC;
- `DOI: `, `URL: `, `ORCID: ` мають рівно один пробіл після двокрапки;
- подвійні розділові знаки та склеювання `DOI:https`, `URL:https` блокують реліз.

### 5. Вставка в ETALON

- ETALON є master shell для секцій, footer, page fields і базових стилів.
- Статті й sections ідуть лише в manifest order.
- Article boundary реалізується canonical `pageBreakBefore`, без dummy blank paragraph.
- Author body не переписується для ущільнення сторінок.
- Попередня стаття має завершитися повністю до SECTION/DOI/UDC наступної.

### 6. Article-boundary gate

Для кожної межі статей довести:

- завершено останній reference item попередньої статті;
- наступна SECTION/DOI/UDC починається в новому paragraph і на новій сторінці;
- немає склеювань на кшталт `...pdfУДК`, `...#Text.УДК`, `...URL:...DOI:`;
- немає page number, section title або DOI всередині тексту попереднього reference item;
- один article start marker відповідає одній manifest article.

Unknown boundary = `BLOCKED`.

### 7. Per-article audit

Для кожної статті порівнювати `raw source → normalized article → final region`:

1. lexical diff;
2. paragraph count/order;
3. run formatting;
4. list semantics;
5. tables;
6. objects/media/order;
7. nested content;
8. author count/order;
9. header semantic tokens, line composition і punctuation;
10. article start page;
11. reference numbering restart;
12. article boundary.

Unknown diff = `BLOCKED`.

### 8. TOC gate

TOC створюється лише після стабілізації тіла.

Кожна manifest article має рівно один entry із:

- canonical English section;
- global article ordinal (`1.`, `2.`, ...);
- усіма й тільки авторами;
- comma + space як separator між авторами;
- title;
- rendered start page.

У TOC заборонені:

- degrees, roles, institutions, city/country;
- DOI/UDC;
- annotation/body text;
- semicolon як separator;
- пропущений автор;
- missing/duplicate ordinal або page;
- неправильна section assignment;
- нумерація учасників `SPECIAL THANKS` / free listeners як статей.

`SPECIAL THANKS` — окремий ненумерований блок після останньої article entry.

TOC parity перевіряє не лише дані, а й геометрію:

- кількість TOC-сторінок;
- шрифт/міжрядковий інтервал;
- відступ між section heading та entries;
- висячі відступи ordinal/authors/title;
- праву позицію page number;
- перенос довгих author lists і titles.

Після матеріалізації TOC виконати повторний render і повторно визначити page starts. Якщо сторінки змінилися — перебудувати TOC до convergence або блокувати run.

### 9. Reference-block gate

Для кожної статті:

- heading відповідає мові статті: `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:` або `REFERENCES`;
- heading не відокремлений від item 1 порожніми абзацами;
- paragraph spacing задається стилем, а не blank paragraphs;
- numbering починається з `1.` заново для кожної статті;
- використовується окремий numbering instance або доведений restart override;
- format — `%1.`; item order і текст незмінні;
- hanging indent, tab stop, line spacing і after/before spacing відповідають published body profile;
- наявний `URL:` або `DOI:` не перекласифіковувати лише через вигляд адреси;
- два різні джерела не можуть злитися в один numbered paragraph;
- reference list не може захопити початок наступної статті.

### 10. Caption and object-flow gate

Порівнювати не пікселі рисунка, а його функцію в макеті:

- canonical punctuation: `Рис. 1.`, `Таблиця 1.`, `Fig. 1.`, `Table 1` відповідно до мови й published fixture;
- пробіл після скорочення та номера;
- caption/source note не відриваються від об'єкта;
- object extent/crop/anchor не створює зайвої або відсутньої сторінки;
- таблиця чи рисунок не перекриває page number і не розриває шапку наступної статті.

### 11. Per-article pagination gate

Зберігати `article_start_page_vector.json`.

- Для реконструкції 136/137 вектор має відповідати published PDF після однакового виключення обкладинки/службових сторінок.
- Першопричину дрейфу шукати в TOC geometry, header composition, blank paragraphs, references spacing, captions і article boundaries.
- Загальна кількість сторінок не замінює per-article vector.

### 12. Published-body parity gate

Побудувати reference profile з опублікованих 136/137 для регіону `TOC → last references`.

Порівнювати:

- TOC content і geometry;
- section assignment і section-heading geometry;
- DOI/UDC/author/title/annotation sequence;
- праве вирівнювання й line composition шапки;
- коми, двокрапки, пробіли після labels;
- paragraph spacing, indents, line density;
- table/caption/source-note geometry;
- reference headings, restart numbering і spacing;
- article-boundary cleanliness;
- article start-page vector.

Parity report має розділяти:

- hard fidelity failures;
- structural/content mismatches;
- punctuation/line-composition mismatches;
- layout deviations;
- intentional exceptions.

### 13. Render gate

Після кожної значущої серії змін:

1. render DOCX → PDF/PNG;
2. переглянути кожну сторінку body region при 100%;
3. перевірити TOC, шапки, коми, tables, clipping, captions, references, page numbers, article transitions і blank pages;
4. після TOC/page updates — повторний render;
5. порівняти regression fixtures 136/137 сторінка-в-сторінку від TOC до останніх references.

## Фінальний fail-closed gate

`PASS` можливий лише коли:

- всі articles mapped;
- unapproved text changes = 0;
- missing paragraphs/tables/objects/captions/formulas = 0;
- author count/order mismatches = 0;
- run-emphasis mismatches = 0;
- numbering-definition mismatches = 0;
- header semantic-token mismatches = 0;
- header punctuation mismatches = 0;
- missing/duplicate TOC rows = 0;
- TOC author/section/ordinal/page mismatches = 0;
- special-thanks entries misnumbered as articles = 0;
- reference restart failures = 0;
- blank paragraphs after reference headings = 0;
- article-boundary concatenations = 0;
- caption punctuation mismatches = 0;
- published-body parity reviewed;
- full body render review passed.

Якщо будь-який пункт не доведений, статус `REVIEW` або `BLOCKED`, але не `PASS`.

## Обов'язкові артефакти релізу

- final journal DOCX;
- final rendered PDF;
- final QA JSON;
- per-article text/run/table/object audits;
- author-header composition and punctuation report;
- TOC entry/geometry audit;
- reference restart/spacing audit;
- article-boundary audit;
- caption/object-flow audit;
- article start-page vector;
- published-body parity JSON;
- render evidence summary;
- versioned skills ZIP + changelog.

## Done when

Реліз доведено на рівні кожної статті та всього body region: нуль непогоджених втрат, повний TOC із правильними авторами, секціями, нумерацією й сторінками, шапки перенесені з правильною композицією рядків і пунктуацією, references перезапускаються з 1 без зайвих blank paragraphs, межі статей чисті, а внутрішня верстка максимально наближена до опублікованих 136/137 без зміни авторського змісту.
