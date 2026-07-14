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


## v3.5 article-scoped UDC gate

- Every `Назва1` article must have exactly one literal `УДК`/`UDC` marker in its own frontmatter.
- A marker from another article and a DOI paragraph using the UDC style are false positives and must not satisfy the gate.
- Missing UDC launches generation immediately; no generation packet means `UDC_GENERATION_NOT_RUN`.
