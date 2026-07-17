# Body-parity аналіз збірок 136 і 137

Дата аналізу: 2026-07-17  
Виправлена редакція: 3.3.1

## Межі аналізу

Цей документ оцінює тільки те, що формує зміст журналу й робить journal skill:

- `TABLE OF CONTENTS`;
- нумерацію статей і сторінок;
- секційні заголовки;
- DOI/UDC;
- авторські шапки, переноси, вирівнювання та пунктуацію;
- назви, annotation/keywords;
- основний текст;
- таблиці/рисунки як елементи потоку, без оцінювання пікселів зображення;
- captions/source notes;
- списки джерел;
- межі між статтями;
- стартові сторінки статей.

Не оцінюються обкладинка, титульно-службові сторінки до TOC і фінальна службова сторінка. ETALON у цій зоні є сирою заготовкою, а не publication reference.

## Порівнювані матеріали

### Конференція 136

- Published: `Conference136.pdf`.
- Our build: `JOURNAL_136_FINAL_RELEASE_v33.docx`, render 96 pages.

### Конференція 137

- Published: `Conference137.pdf`.
- Our builds: `137.docx`, `JOURNAL_137_CAMBRIDGE_CORRECTED_V7_TOC_CORE55.docx` і ранні smoke fixtures.

## Головний висновок

Внутрішнє тіло 136 значно ближче до published reference, ніж показував попередній висновок. Основні регресії лежать не в загальній структурі статті, а в деталях, які безпосередньо створює skill:

1. TOC geometry і класифікація записів;
2. повнота авторів і правильність секції;
3. композиція рядків author header;
4. кінцеві коми в продовжувальних metadata lines;
5. пробіли в captions і labels;
6. reference hanging indent/spacing;
7. чисті межі між останнім джерелом і наступною статтею.

Тому parity має бути corpus-driven і granular: не «документ схожий загалом», а row-by-row, author-by-author, paragraph-by-paragraph.

# Conference 136

## 1. TOC: головне джерело зсуву пагінації

Published TOC займає три сторінки. Наш TOC займає дві сторінки, бо entries ущільнені сильніше. Через це перша стаття має printed page 4 у нашій збірці та page 5 у published PDF, хоча саме тіло першої статті далі йде майже синхронно.

### Виявлені content mismatches

- У нашому entry 8 вказано лише `Косинський П. І.`, тоді як published entry містить `Косинський П. І., Тимонін Ю. О.`.
- Наш entry 10 опинився в `PHYSICAL CULTURE, SPORTS AND PHYSICAL THERAPY`, тоді як published reference має `PHILOLOGY AND JOURNALISM`.
- Наші free listeners / special-thanks participants продовжують article numbering як 25–30. У published reference article numbering завершується на 24, а подяки оформлено окремим ненумерованим блоком.
- Заголовки, author rows і titles у нашому TOC мають менші вертикальні інтервали, тому на першій сторінці вміщується 13 entries замість 9.

### Правило

TOC entry будується тільки з manifest article record. Participants, special thanks, reports without full article status і службові згадки не можуть отримувати article ordinal.

## 2. Author header: загальна схема правильна, деталі відрізняються

У першій статті 136 наш build правильно відтворює базову геометрію published reference:

- centered uppercase section heading;
- UDC зліва;
- author/PIP block справа;
- centered title;
- annotation і keywords нижче.

Тобто змінювати шапку на ліве вирівнювання або робити іншу глобальну схему не потрібно.

### Точні відмінності на fixture Гнисюк / Сімкова

Published:

```text
Гнисюк Анастасія Олексіївна
здобувачка вищої освіти
Сімкова Тетяна Олексіївна
науковий керівник,
к.е.н., доцент,
Національний університет «Київський авіаційний інститут»
м. Київ, Україна
```

Our build:

```text
Гнисюк Анастасія Олексіївна
здобувачка вищої освіти
Сімкова Тетяна Олексіївна
науковий керівник
к.е.н., доцент
Національний університет
«Київський авіаційний інститут»
м. Київ, Україна
```

Різниця:

- пропущено кінцеві коми на двох продовжувальних рядках;
- цілісну назву установи штучно розбито на два paragraphs;
- зайвий paragraph додає вертикальну висоту шапки.

### Fixture Матвієнко / Бобиль

Published зберігає:

```text
кафедра математичної інформатики,
факультет комп’ютерних наук та кібернетики,
Київський національний університет імені Тараса Шевченка
м. Київ, Україна
```

Тут коми означають, що metadata chain граматично продовжується. Skill не повинен ані видаляти ці коми, ані перетворювати всі рядки на речення з крапками.

## 3. Caption punctuation

У published fixture використано `Рис. 1.`. У нашій збірці — `Рис.1.`. Потрібен один пробіл після скорочення й після номера згідно з published pattern.

Це малий дефект, але він легко перевіряється детерміновано й має входити до caption gate.

## 4. References

Позитивне: у 136 кожен список джерел перезапускається з `1.` і мовні headings загалом правильні.

Відмінність у spacing/numbering geometry:

- на першій references page нашої збірки вміщується 3 items;
- у published reference на відповідній сторінці вміщується 4 items;
- у нашому DOCX після references heading є зайві blank paragraphs;
- hanging indent/tab stop і line spacing дещо ширші.

Правило: після heading не створювати пустих paragraphs; використовувати style spacing. Кожна стаття отримує окремий numbering instance або доведений restart override з `start=1`.

# Conference 137

## 1. TOC punctuation і numbering

Published TOC має для кожної статті:

```text
ordinal + authors separated by comma + title + rendered page
```

Наприклад, кілька авторів перелічуються через `, `, а не через `; `.

У V7 fixture автори подекуди розділялися крапками з комою, а ordinals/pages не були повністю матеріалізовані. Це має блокувати release незалежно від того, чи всі назви присутні.

## 2. Author-header composition не зводиться до одного шаблону

Опублікований корпус показує кілька допустимих композицій.

### Злакоман

Published і пізня `137.docx` близькі:

```text
Злакоман Ігор Миколайович
кандидат юридичних наук
Independent Researcher
м. Одеса, Україна
ORCID: ...
```

Ранній V7 зливав degree, researcher status і location. Це regression fixture для заборони cross-field concatenation.

### Живко та співавтори

Published використовує окремий блок для кожного з п’яти авторів: name → qualification/role → institution → location. У нашій `137.docx` частина qualification, institution і location зібрана в один довгий paragraph через коми.

Проблема не в самих комах, а в тому, що paragraph стає надто довгим і втрачає published line rhythm. Авторські межі та синтаксичні групи мають бути явними.

### Маєр

Published компактно поєднує:

```text
вихователь-методист ЗДО «Казковий світ»
Зимноводівської сільської ради
Львівського району Львівської області
```

Наш build розбиває role і коротку назву ЗДО на окремі paragraphs, а район/область дробить сильніше. Отже, blanket rule «кожне поле окремо» теж неправильне.

### Александрова та Сергієнко / Волкова

Пізня `137.docx` уже ближча до published reference: qualification, department, institution і location розділено по природних межах; автори не зливаються. Цю поведінку слід зберегти як позитивний fixture.

## 3. Article-boundary concatenation

У `137.docx` трапляються структурні склеювання:

- останній URL попередньої статті одразу переходить у `УДК`;
- `...#Text.УДК...`;
- URL попереднього reference переходить у `DOI:` наступної статті;
- `DOI:https://...` без пробілу.

У published PDF наступна стаття починається окремим блоком і на окремій сторінці. Це має бути hard blocker, бо проблема змінює і текстову цілісність, і пагінацію.

## 4. Reference normalization

Published corpus не вимагає перетворювати кожне `https://doi.org/...` на label `DOI:`. В окремих references URL залишається bare link або з авторським `URL:`.

Правило:

- зберігати наявний label;
- не перекласифіковувати за доменом;
- додавати label лише за окремим canonical/editorial rule;
- не зливати два bibliography records в один numbered paragraph.

# Нові обов’язкові gates

## A. Body-only parity boundary

Порівнювати `TABLE OF CONTENTS → last article references`. Обкладинка й службова оболонка не впливають на body-parity score.

## B. TOC record gate

Для кожної article record:

- одна правильна section;
- один global ordinal;
- повний author list;
- comma separator;
- title;
- rendered page;
- жодних numbered special-thanks participants.

## C. Header composition and punctuation gate

- right-aligned PIP block;
- author boundaries immutable;
- corpus-driven grouping of degree/role/department/institution/location;
- trailing comma тільки для продовження metadata chain;
- no final punctuation after name or location;
- one space after `DOI:`, `URL:`, `ORCID:`.

## D. Reference restart and spacing gate

- new numbering instance/restart at 1 per article;
- no blank paragraph after references heading;
- published hanging indent/tab/line-spacing profile;
- no merged bibliography items.

## E. Article-boundary lexical gate

Block patterns where SECTION/DOI/UDC begins in the same paragraph or token stream as the final reference of the previous article.

## F. Caption punctuation gate

Corpus fixtures validate `Рис. 1.`, `Таблиця 1.`, `Fig. 1.`, `Table 1` and the surrounding spacing.

## G. Per-article start-page vector

The vector is interpreted only after TOC geometry is stabilized. For 136 the first body-page mismatch is primarily a TOC-page-count mismatch, not evidence that the first article body is globally malformed.

# Corrected assessment

The strongest part of our pipeline is article-body preservation. The weakest part is deterministic editorial composition around it:

- TOC record classification and geometry;
- exact author list;
- semantic line composition;
- continuation commas;
- references spacing and restart;
- article boundaries.

The next implementation should encode these as structural data and deterministic tests rather than asking an LLM to imitate a page visually.
