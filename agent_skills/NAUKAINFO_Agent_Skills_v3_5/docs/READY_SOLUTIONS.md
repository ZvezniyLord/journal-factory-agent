# Готові стандарти й компоненти, які використано

1. **Agent Skills open format** — папка зі `SKILL.md`, scripts, references і assets; progressive disclosure дозволяє мати багато скілів без постійного завантаження всього контексту.
2. **Model Context Protocol (MCP)** — стандартний спосіб дати агенту tools/resources/workflows. Один MCP server можна підключати до різних агентних клієнтів.
3. **OpenAI Agents SDK** — готовий runtime із tool loop, guardrails, handoffs, sessions, human-in-the-loop і tracing. Це опційний host; skill pack не прив’язаний до одного постачальника моделі.
4. **Наявний Journal Builder** — уже готовий доменний backend. Його модулі використовуються як tools; не створюється паралельний DOCX engine.

## Чого не рекомендовано

- Великий «всемогутній» skill на тисячі рядків.
- Десятки мікроскілів для одного кроку.
- Дозвіл skill напряму змінювати raw files.
- Сторонні community skills без перевірки коду та дозволів.
- LLM як єдине джерело truth для UDC, matching або quality gate.

## Перевірені у запуску 2026-07-09

5. **Evidence matching author + title** — стаття вважається знайденою лише коли ПІБ автора та назва статті підтверджені всередині DOCX; filename/folder використовуються тільки як допоміжні ознаки.
6. **ETALON structural slot insertion** — робоче місце вставки визначено перед paragraph-level section break після сторінки `TABLE OF CONTENTS`. Тестова стаття з 2 таблицями і 4 рисунками вставлена без втрати об’єктів; хвостова службова сторінка збережена.

7. **Effective table-format fidelity** — у тестовому ETALON стиль `Normal` мав first-line indent 567 twips, через що 49 table paragraphs успадкували відступ, хоча direct property була порожня. Перевірене рішення: source↔target audit effective formatting і прямий `w:firstLine="0"` лише в клітинках; після save/re-open залишкових відмінностей немає.


## Semantic first-line-indent cleanup

Use `scripts/semantic_paragraph_roles.py` to classify and repair protected article roles without touching ordinary body indentation.

## SmartArt and shape transfer

Use `scripts/normalize_11_with_shapes.py` before insertion and `scripts/shape_object_fidelity.py` after insertion. Verified on the Hnysiuk motivation diagram.


## Multiple articles in one ETALON

Use `naukainfo-multi-article-assembly` and `scripts/multi_article_reference_restart.py`. Compose semantic article ranges, assign a page break before each subsequent article, then rebuild reference numbering per article and render before generating the TOC.

## v2.9 verified solutions

- Recover omitted raster images from a legacy OLE `.doc` while retaining source hashes and visual evidence.
- Reconstruct a stable inline five-figure sequence for a legacy article without rewriting prose.
- Recognize `Таблиця` without a number and format it without inventing one.
- Normalize German and English reference markers while preserving reference content/order.
- Rebuild TOC author rows from final body styles and detect missing/extra names.
