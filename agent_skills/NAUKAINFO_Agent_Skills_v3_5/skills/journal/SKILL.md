---
name: journal
description: Єдиний проєктний скіл для повного циклу NAUKAINFO Journal Builder у проєкті «Дирежор»: приймання матеріалів, підготовка статей, збирання журналу в ETALON, збереження авторського тексту/форматування/об’єктів, зміст, нумерація сторінок, рендер, глибокий аудит і реліз. Активується лише явно в цьому проєкті та чаті.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; python-docx; lxml; LibreOffice; NAUKAINFO Journal Builder.
metadata:
  author: naukainfo
  version: "3.5.0"
  priority: "0-critical"
  scope: "Дирежор / NAUKAINFO Journal Builder only"
---

# ЖУРНАЛ — єдиний головний скіл

## Нульовий gate: обов’язкові виробничі активи

Перед читанням архіву статей або будь-якою генерацією виконавець зобов’язаний знайти у переданій папці такі точні активи:

- `02_TEMPLATES_REQUIRED/ETALON-JOURNAL.docx`;
- `02_TEMPLATES_REQUIRED/Jurnal.dotx`;
- `01_SKILL_JOURNAL/NAUKAINFO_Agent_Skills_v3_4.zip` або розпакований `skills/journal/SKILL.md`;
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

- шапка: DOI/UDC → рівно один службовий blank після фактичного UDC → AUTOR/pip → blank → title → blank → body;
- standalone `AUTOR` line contains only the person name: remove a terminal comma/semicolon/colon when all degree, role, institution and location text has been moved to following `pip` paragraphs;
- this terminal-punctuation cleanup is a hard global rule for every standalone `AUTOR` paragraph and every TOC author-name cell; after save/reopen, zero author names may end in `,`, `;` or `:`;
- if source UDC/УДК is absent, generate a documented high-confidence UDC proposal from the article subject, insert it as actual `UDC`, and mark `udc_source=generated`; ambiguous classification blocks release for operator review instead of leaving the field absent;
- UDC detection is article-scoped: enumerate every `Назва1` title and require one literal `УДК`/`UDC` marker in that article’s own frontmatter; a UDC in another article or a `DOI:` paragraph using style `UDC` is never evidence; missing marker must trigger generation, and absence of the generation packet is `UDC_GENERATION_NOT_RUN`;
- all degree/status/position/department/institution/city/country/ORCID lines between UDC and title must be recognized as actual `pip`; remove inherited list numbering, bullets, tabs and paragraph indents from every frontmatter paragraph;
- table title immediately after `Таблиця N` / `Table N` must use the actual ETALON `РисПід` style (`styleId af6`), not a visually similar `Normal` paragraph;
- email/phone/messenger видаляються лише з шапки; ORCID зберігається;
- author-written section notes видаляються;
- `Анотація.`/`Abstract.` та `Ключові слова:`/`Keywords:` нормалізуються без зміни тексту;
- між анотацією і keywords немає blank; після keywords рівно один blank;
- table/figure/caption/source blocks нормалізуються без first-line indent;
- recursively обробляти text boxes/shapes/nested tables;
- references розпізнавати маркером або сильними terminal-list ознаками, але невпевненість = stop/review;
- a reference paragraph may use automatic `REFER` numbering or a manually typed numeral in source, never both in final; rebuild one logical citation per `REFER` paragraph, remove the typed leading numeral, compare entry count with source, then save/reopen and assert zero duplicate visible numbers;
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
- Якщо manifest містить вільних слухачів, фінальна секція залишається **в тій самій 3-column TOC table**, а не виноситься на окрему сторінку.
- Її точний видимий заголовок: `SPECIAL THANKS FOR ACTIVE PARTICIPATION IN THE SCIENTIFIC AND PRACTICAL CONFERENCE ARE EXTENDED TO THE FOLLOWING PARTICIPANTS:`. Заголовок займає один merged row усіх трьох колонок і має actual style `TabSEC`.
- Після заголовка створюється **один** listener row: перша й третя клітинки порожні, у другій усі підтверджені імена в manifest order перераховані через `, `; абзац має actual style `TabPIP`, left/firstLine = 0, без tabs, numbering і page number.
- Заборонені окремі пронумеровані listener rows, окрема listener page, `Normal` style і абзацний відступ у listener names cell.
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
- standalone AUTOR/TOC terminal punctuation defects = 0;
- frontmatter list/bullet/indent artifacts = 0;
- missing required UDC fields = 0 for every article-local frontmatter block, except explicitly BLOCKED ambiguous cases;
- every article title has exactly one literal UDC/УДК marker before it; DOI-styled-as-UDC false positives = 0;
- reference auto-number + typed-number duplicates = 0 and reference entry count matches source;
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
- validated references freeze: якщо `REF-TITLE`/`REFER` structural audit уже PASS, corrective runs не перебудовують і не чистять цей блок повторно без нового reference defect;
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
