# PROJECT_STATUS

Оновлено: 2026-07-19

## Продукт

Production Journal Builder: сирі матеріали конференції → DOCX → PDF → QA reports.

## Поточний цикл

- Гілка: `agent/journal-builder-95`.
- Conference 95, iteration 2.
- Профіль: `legacy_14pt`.
- Артефакти передано у стан `READY_FOR_REVIEW`; Codex не встановлює `ACCEPTED`.

## Виконано

- реальний ZIP інвентаризовано без коміту RAW у Git;
- auto-manifest класифікує статті, службові документи й дублікати за текстовими та структурними доказами;
- 34 статті зіставлено з confidence і provenance;
- legacy `.doc` читаються read-only Word COM через короткі ізольовані шляхи;
- article preparation прибирає лише доведений embedded application tail;
- стилі `Jurnal.dotx`, геометрія ETALON і профіль `legacy_14pt` застосовано кодом;
- source-to-final fidelity перевіряє порядок абзаців, таблиці, textboxes, media, charts і embeddings;
- створено DOCX і PDF на 241 сторінку;
- дві чисті збірки мають однакові manifest, текст і object payloads;
- 61 regression-тест пройшов;
- контрольовану чистку виконано окремим комітом.

## Поточні blockers

1. Службові сторінки ETALON не параметризовані для Conference 95 та містять застарілі дані різних конференцій.
2. TOC field відсутній, тому 34 записи змісту не сформовано.
3. Наскрізна пагінація не покриває PDF-сторінки 1–89.
4. Потрібен окремий direct-run font-size audit перед production gate.

Відсутність офіційного `Conference95.pdf` не є blocker і publication parity у цій ітерації не вимагається.

## Наступний технічний крок

Дочекатися рішення Reviewer у `coordination/CYCLE_STATE.json`. Якщо буде `CHANGES_REQUESTED`, виконати новий `next_action` без конференційного винятку `if conference_id == 95`.

## Gate переходу до Conference 96

Conference 95 переходить у PASS лише коли:

- усі manifest-статті включені рівно один раз;
- source body text parity = 100%, object loss = 0;
- службові сторінки відповідають manifest/config конференції;
- TOC і друковані сторінки узгоджені;
- DOCX успішно рендериться;
- критичних blockers немає;
- повторний чистий build дає той самий результат за правилами та вхідними SHA.

## Другий повний прохід

Після проходу всіх доступних архівів 95–135 виконується повторна regression-матриця з чистого workspace та незмінним ruleset.
