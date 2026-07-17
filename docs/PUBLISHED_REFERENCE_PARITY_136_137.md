# Самоаналіз збірок 136 і 137 проти опублікованих версій

Дата аналізу: 2026-07-17

## Межі аналізу

- Перша сторінка/обкладинка виключена з оцінки.
- Піксельний вигляд самих ілюстрацій не оцінювався.
- Враховувалися: внутрішня верстка, службові сторінки, зміст, стилі, порядок і сегментація авторського блоку, пагінація, розміщення таблиць/рисунків у потоці, підписи, references, секційні заголовки та фінальна службова сторінка.
- Авторська текстова й об'єктна цілісність залишається жорстким обмеженням. Наближення до опублікованого вигляду не може виправдовувати втрату змісту.

## Порівнювані матеріали

### Конференція 136

- Опублікований еталон: `Conference136.pdf`, 96 PDF-сторінок.
- Наш результат: `JOURNAL_136_FINAL_RELEASE_v33.docx`.

### Конференція 137

- Опублікований еталон: `Conference137.pdf`, 84 PDF-сторінки.
- Наш основний результат: `JOURNAL_137_CAMBRIDGE_CORRECTED_V7_TOC_CORE55.docx`, 90 сторінок після рендеру.
- Ранні smoke-збірки розглядалися лише як негативні regression fixtures.

## Загальний висновок

Найслабшим місцем наших збірок було не перенесення основного тексту, а **release parity**: службові дані, реальний зміст, семантичне розбиття шапки, точна пагінація, ізоляція фінальної сторінки й відсутність залишків старого ETALON. Наявні fidelity-gates добре захищають авторське тіло, але ще не доводять, що документ схожий на фактично опубліковану серію.

Потрібна двоцільова модель:

1. **Hard constraint:** нуль непогоджених втрат або переписування авторського матеріалу.
2. **Optimization target:** серед усіх безпечних варіантів обирати той, що мінімізує структурно-верстальну відстань до опублікованого корпусу NAUKAINFO.

## Конференція 136: критичні розбіжності

### 1. Повне протікання метаданих старого ETALON

У `JOURNAL_136_FINAL_RELEASE_v33.docx` залишилися чужі службові дані:

- `SCIENCE IN THE MODERN WORLD` замість `SCIENCE AND GLOBAL DEVELOPMENT`;
- January 19-21, 2026 замість June 28-30, 2026;
- Cambridge замість Barcelona;
- `conference?id=91` замість `conference?id=136`;
- DOI `conf-91-2026` замість `conf-136-2026`;
- старий ISBN;
- `0000000 p.` замість фінального обсягу;
- інша дата затвердження.

Це означає, що перевірка наявності ETALON недостатня. Потрібен **stale-template fingerprint gate**, який сканує всю передню й фінальну службову частину та блокує реліз при будь-якому токені іншої конференції.

### 2. Зміст фактично не був матеріалізований як опублікований TOC

Після `TABLE OF CONTENTS` у нашому DOCX одразу з'являються УДК, авторська шапка й тіло першої статті. В опублікованій версії 136 зміст містить:

- англомовні секційні заголовки;
- наскрізний номер статті;
- тільки імена авторів;
- назву статті;
- фактичний номер стартової сторінки.

Отже, TOC-gate має перевіряти не лише наявність таблиці/стилів, а повноту кожного рядка й відсутність body-параграфів у TOC-регіоні.

### 3. Release shell не був зв'язаний з одним manifest

Правильний авторський вміст співіснував із чужою конференційною оболонкою. Це свідчить, що article manifest і publication manifest були незалежними. Потрібен один immutable `publication_manifest.json`, з якого беруться title, dates, city, country, conference id, conference DOI, ISBN, approval date, bibliographic page count і рекомендоване цитування.

## Конференція 137: вимірювані розбіжності

### 1. Розмір і пагінація

- Наш рендер: 90 сторінок.
- Опублікований PDF: 84 сторінки.
- У нашому бібліографічному блоці було `84 p.`; у публікації — `81 p.`.

Загальна кількість сторінок не є достатнім показником. Потрібно порівнювати **вектор стартових сторінок статей**. Наприклад:

- стаття Мінькова: наша версія починалася на сторінці 17, опублікована — на 18;
- стаття Злакомана: обидві версії починалися на 26.

Отже, дрейф локальний і спричинений сегментацією та щільністю окремих блоків, а не одним глобальним масштабом.

### 2. Службова сторінка

У нашому результаті були:

- `This edition was prepared for publication on July 12, 2026`;
- `ISBN: assignment pending`;
- `Author. Article title` у рекомендованому цитуванні;
- 84 p.

В опублікованому результаті:

- затвердження July 16, 2026;
- ISBN `978-617-8680-82-4`;
- конкретний зразок цитування;
- 81 p.

Будь-які `pending`, `0000000`, generic author/title placeholders або невідповідні дати мають бути release blockers.

### 3. TOC

Наш V7 TOC містив авторів і назви, але не мав стабільно матеріалізованих номерів статей та сторінок. Також застосовувалися крапки з комою між авторами.

Опублікований TOC має:

- `1.`, `2.`, ... перед авторами;
- page number для кожної статті;
- коми між авторами;
- відсутність ступенів, посад та установ;
- секційні заголовки тільки англійською.

Потрібен row-level gate: `section + ordinal + authors + title + page` для кожної статті.

### 4. Семантичне розбиття авторського блоку

У нашій версії окремі рядки зливалися:

- `кандидат юридичних наук Independent Researcher м. Одеса, Україна`;
- `юридичний консультант ТОВ «Укргазнафта» м. Слов'янськ, Україна`.

В опублікованому PDF ці елементи стоять окремими абзацами. Це не просто косметика: злиття змінює ритм сторінки, перенос назви й старт наступної статті.

Правило: короткі PIP-рядки не можна конкатенувати. Degree/role, institution і city/country — окремі paragraphs, якщо вони окремі у джерелі або manifest.

### 5. Over-normalization references

У нашому V7 частина DOI-посилань була семантично перейменована з `URL:` на `DOI:`. Опублікований корпус допускає обидва варіанти й часто зберігає авторську мітку навіть для `https://doi.org/...`.

Правило: не перекласифіковувати label лише за виглядом URL. Додавати відсутню мітку можна, але змінювати наявну `URL:` на `DOI:` — тільки за явним редакторським рішенням.

### 6. Фінальна службова сторінка

В одному з наших результатів tail-текст приєднувався одразу після останнього reference block. В опублікованій версії це окрема фінальна сторінка.

Потрібен gate:

- tail починається з нової сторінки;
- перебуває у захищеній останній секції;
- не містить page number основного тіла;
- остання стаття не захоплює tail-параграфи;
- tail metadata дорівнює publication manifest.

## Що вже було правильним

- Перехід до ETALON як master shell правильний.
- Пріоритет lexical/object fidelity правильний і має залишатися абсолютним.
- Ідея двопрохідного TOC і повторного рендеру правильна.
- Окремі article starts у V7 вже наблизилися до опублікованої пагінації.
- DOI/UDC → author block → title → annotation відповідає опублікованому 137, якщо PIP не зливається.
- Канонічні англомовні section headings відповідають серії.

## Нові обов'язкові gates

### A. Publication manifest gate

Обов'язкові поля:

- conference_number;
- conference_title;
- date_range;
- city;
- country;
- conference_url;
- conference_doi;
- isbn;
- approval_date;
- bibliographic_page_count;
- recommended_citation;
- final_service_page_text.

Жодне поле не можна брати із залишкового ETALON-тексту.

### B. Stale-template fingerprint gate

Сканувати front matter і tail на:

- інші conference id/DOI;
- інші дати/міста/назви;
- старі ISBN;
- `0000000`, `pending`, `Author. Article title`;
- старі approval dates.

Будь-який збіг = `BLOCKED`.

### C. Published-reference parity gate

Порівняння з corpus profile 136/137 після виключення:

- першої сторінки;
- піксельного вмісту авторських ілюстрацій.

Але зберігаються в оцінці:

- місце, розмір і обтікання object cluster;
- підпис і source note;
- вплив object cluster на пагінацію.

### D. TOC row completeness gate

Для кожної manifest article:

- рівно один TOC row;
- правильний ordinal;
- автори без ролей/установ;
- canonical comma separator;
- title;
- rendered start page;
- жодних UDC/DOI/body paragraphs у TOC.

### E. Per-article pagination gate

Зберігати `article_start_page_vector.json`. Для відтворення 136/137 він має точно збігатися з published reference. Для нових конференцій виявляти аномалії за профілем: надмірні порожні зони, випадкові blank pages, злиті header paragraphs, detached captions.

### F. PIP segmentation gate

Заборонити автоматичне об'єднання degree/role, institution, city/country, supervisor lines. Порівнювати semantic line signature source → normalized → final.

### G. Tail isolation gate

Фінальна службова сторінка окрема, незмішана з references і синхронізована з publication manifest.

### H. Reference-label preservation gate

Existing `URL:`/`DOI:` labels зберігаються. Автоматичне reclassification за regex заборонене.

## Рекомендовані технічні артефакти

- `schemas/publication-manifest.schema.json`;
- `schemas/published-reference-profile.schema.json`;
- `scripts/build_published_reference_profile.py`;
- `scripts/audit_publication_metadata.py`;
- `scripts/audit_toc_rows.py`;
- `scripts/compare_article_start_pages.py`;
- `scripts/audit_pip_segmentation.py`;
- `scripts/audit_tail_isolation.py`;
- regression fixtures для Conference136 і Conference137;
- один JSON-звіт `published_reference_parity.json`.

## Мінімальні критерії PASS

- stale-template tokens = 0;
- placeholders = 0;
- publication metadata mismatches = 0;
- missing/duplicate TOC rows = 0;
- TOC page mismatches = 0;
- merged PIP semantic lines = 0;
- tail isolation failures = 0;
- unknown reference-label changes = 0;
- непогоджені text/object diffs = 0;
- full render review пройдено після останньої матеріалізації TOC.

## Головний урок

ETALON і fidelity audit є необхідними, але не достатніми. Реліз має доводити три речі одночасно:

1. авторський матеріал не пошкоджено;
2. publication metadata належить саме цій конференції;
3. внутрішня верстка й пагінаційна поведінка відповідають реально опублікованому корпусу 136/137, а не лише формальним стилям DOCX.
