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

- Перевірка виконується окремо для кожної статті за її `Назва1`/manifest ID. Наявність УДК в іншій статті не закриває вимогу.
- Рядок `DOI:` навіть зі стилем `UDC` не є маркером УДК; потрібен буквальний префікс `УДК` або `UDC`.
- Якщо маркер відсутній, pipeline зобов’язаний створити UDC lookup/generation packet; відсутність такого packet має код `UDC_GENERATION_NOT_RUN`.
- Якщо UDC відсутній, збірка зупиняється зі статусом `UDC_LOOKUP_REQUIRED`.
- Назва, анотація, ключові слова та офіційна секція передаються онлайн-агенту для evidence-based пошуку UDC; відповідь містить джерела, confidence, альтернативи та `needs_operator_review: true`.
- Вставлення дозволене лише після підтвердження оператора.
- UDC має фактичний стиль `UDC`; після нього рівно один порожній абзац — не нуль і не більше одного.
- Окремий рядок ПІБ після розділення шапки не завершується комою/крапкою з комою/двокрапкою, якщо службові дані вже перенесені в наступні `pip` абзаци.

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
- Вільні слухачі залишаються у тій самій TOC table: exact heading `SPECIAL THANKS FOR ACTIVE PARTICIPATION IN THE SCIENTIFIC AND PRACTICAL CONFERENCE ARE EXTENDED TO THE FOLLOWING PARTICIPANTS:` у merged `TabSEC` row; один наступний `TabPIP` row містить усі імена через кому без номерів і сторінок.
- Перевірений reference pipeline (`REF-TITLE` + `REFER`, fresh numbering, Ctrl+Space-equivalent cleanup) вважається frozen baseline: після PASS його не перебудовувати у вузьких корекційних проходах без нового дефекту.


## Single skill rule

The public activation name is `journal` / «журнал». All former rules are internal modules. No module may be applied in another project/chat without explicit activation of the master skill.


## Release 3.4 — protected frontmatter and bibliography rules

- Standalone author names and TOC author names never retain a source comma/semicolon/colon after metadata is moved to following lines.
- Missing UDC is not silently tolerated: generate a documented high-confidence proposal or block for review.
- Frontmatter order is DOI/UDC, one blank, AUTOR/pip, one blank, title. All helper metadata is `pip`; bullets and imported indents are forbidden.
- `REFER` style plus a typed source number is a duplicate-number defect. Rebuild one citation per paragraph, remove typed digits, restart automatic numbering at 1, and verify after reopen.
