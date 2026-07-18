# PROJECT_STATUS

Оновлено: 2026-07-19

## Продукт

Production Journal Builder: сирі матеріали конференції → готовий DOCX → готовий PDF → QA reports.

## Поточна гілка

`agent/journal-builder-95`

## Поточна конференція

Conference 95 — ACTIVE.

## Уже є

- безпечна підготовка archive workspace;
- article manifest і source snapshots;
- канонічний journal skill;
- ETALON і DOTX як обов’язкові активи;
- допоміжний RAW↔golden analyzer у draft PR №5;
- правила багатoагентної роботи у `AGENTS.md`;
- команда для Codex у `CODEX.md`.

## Ще потрібно для Conference 95

1. Реальний RAW `95.zip` доступний на host.
2. Production header parser.
3. Lossless DOCX/XML transfer статей.
4. Імпорт і перевірка стилів `Jurnal.dotx`.
5. Assembly у `ETALON-JOURNAL.docx`.
6. TOC, section breaks, footer і page fields.
7. Render DOCX→PDF.
8. Source→final text/object fidelity.
9. Publication parity проти офіційного `Conference95.pdf`.
10. Regression fixtures і final gate.

## Поточний blocker

У хмарному конекторі сирі байти `95.zip` повертають HTTP 403. Для реального build потрібен локальний файл на Windows/VM або host test через `docs/HOST_TEST_PROTOCOL.md`.

Це не блокує розробку архітектури, модулів, тестів і fixtures.

## Наступний технічний крок

Реалізувати production article preparation та lossless OpenXML merge, після чого створити host request для першого реального build Conference 95.

## Gate переходу до Conference 96

Conference 95 переходить у PASS лише коли:

- усі manifest-статті включені рівно один раз;
- source body text parity = 100%;
- object loss = 0;
- TOC і друковані сторінки узгоджені;
- DOCX успішно рендериться;
- критичних blocker немає;
- повторний чистий build дає той самий результат за правилами та вхідними SHA.

## Після першого проходу

Після проходу всіх доступних архівів 95–135 виконується другий чистий regression-прохід по всій матриці одним ruleset.
