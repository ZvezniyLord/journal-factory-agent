# PROJECT_STATUS

Оновлено: 2026-07-19

## Продукт

Production Journal Builder: сирі матеріали конференції → DOCX → PDF → QA reports.

## Поточний цикл

- Гілка: `agent/journal-builder-95`.
- Conference 95, iteration 3.
- Профіль: `legacy_14pt`.
- Артефакти підготовлено до `READY_FOR_REVIEW`; Codex не встановлює `ACCEPTED`.

## Виконано

- auto-manifest зберіг прийняті метрики: 34 статті, 6 дублікатів, 99 службових файлів, 0 REVIEW/BLOCKED;
- metadata config детерміновано матеріалізує front/back matter для Oxford Conference 95;
- stale-marker audit не знаходить New York, Cambridge, Conference 91 або старих реквізитів;
- справжнє Word TOC містить 34/34 записи статей і стабілізується за два однакові проходи;
- стаття 1 починається на physical/printed page 6, далі пагінація без reset до page 237;
- canonical section mapping не містить конференційних умов;
- post-render typography audit підтверджує 7 532 body-runs із effective size 14 pt;
- fidelity, object preservation, all-pages raster QA і clean rebuild мають PASS;
- 73 regression-тести та compile check пройшли.

## Поточні blockers

Немає. Результат очікує рішення Reviewer.

Відсутність офіційного `Conference95.pdf` не є blocker і publication parity у цій ітерації не вимагається. Packaged LibreOffice renderer недоступний на host через відсутній `soffice`; обов’язковий Microsoft Word COM render і PyMuPDF-аудит усіх сторінок пройшли.

## Наступний технічний крок

Reviewer перевіряє iteration-003 у `coordination/CYCLE_STATE.json`. Codex не переводить конференцію в `ACCEPTED` самостійно.

## Gate переходу до Conference 96

Conference 95 переходить у PASS лише після рішення Reviewer за опублікованими DOCX, PDF, fidelity, TOC, pagination, typography та clean-rebuild reports.

## Другий повний прохід

Після проходу всіх доступних архівів 95–135 виконується повторна regression-матриця з чистого workspace та незмінним ruleset.
