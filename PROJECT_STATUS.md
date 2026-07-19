# PROJECT_STATUS

Оновлено: 2026-07-19

## Продукт

Production Journal Builder: сирі матеріали конференції → DOCX → PDF → QA reports.

## Поточний цикл

- Гілка: `agent/journal-builder-95`.
- Conference 95, iteration 4.
- Профіль: `legacy_14pt`.
- Стан артефактів: `READY_FOR_REVIEW`; Codex не встановлює `ACCEPTED`.
- Official golden PDF обов'язковий і перевірений.

## Виконано

- official TOC зіставлено з RAW: 34/34 статті, 14 редакційних секцій, 0 missing/extra/ambiguous;
- порядок починається з Резнікова, Львовича та Ганзюк;
- TOC займає фізичні сторінки 4–7 з офіційним розподілом `1–8 / 9–17 / 18–29 / 30–34`;
- special-thanks блок розміщено на фізичній сторінці 7;
- усі 34 article bookmarks збігаються з official physical/printed starts;
- перша стаття починається на physical 8 / printed 6;
- Word/PDF мають 248 сторінок, усі 248 перевірено raster-аудитом, порожніх сторінок немає;
- fidelity, object preservation, typography та official corpus/page parity мають `PASS`;
- фінальний clean rebuild відтворив PDF text SHA, TOC/bookmarks і page count; raster delta нижче tolerance;
- 80 regression-тестів і compile check пройшли.

## Поточні blockers

Немає. Результат очікує рішення Reviewer.

## Наступний крок

Reviewer перевіряє iteration-004 у `artifacts/conferences/095/iteration-004`. Перехід Conference 95 у `ACCEPTED` виконує лише Reviewer.

## Другий повний прохід

Після проходу всіх доступних архівів 95–135 виконується повторна regression-матриця з чистого workspace та незмінним ruleset.
