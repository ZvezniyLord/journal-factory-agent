# Conference 95 — iteration 004

Статус: `READY_FOR_REVIEW`, не `ACCEPTED`.

## Результат

- Офіційний PDF обов'язковий і перевірений за SHA-256 `fd16720e1573b4d95073b1f9a9cfc5823342dca26fb9a6ba2841136bde12e2d7`.
- Офіційний TOC розібрано: 14 редакційних секцій і 34 статті, без missing/extra/ambiguous.
- Порядок починається з Резнікова, Львовича та Ганзюк; усі 34 source-файли зіставлено з official TOC.
- TOC займає фізичні сторінки 4–7 з офіційним розподілом статей `1–8 / 9–17 / 18–29 / 30–34`.
- Special-thanks блок розміщено на фізичній сторінці 7.
- Усі 34 article bookmarks збігаються з офіційними фізичними й друкованими стартами; перша стаття починається на physical 8 / printed 6.
- Word COM і PDF мають 248 сторінок; видимі footer-номери `246/246`, порожніх сторінок немає.
- Fidelity і object preservation мають `PASS`: 34/34 статті присутні по одному разу, втрат таблиць, рисунків, chart payloads або embeddings немає.
- Незалежний clean rebuild відтворив той самий PDF text SHA, TOC/bookmarks і 248 сторінок. Raster-різниця — 3 канали сторінки 179 (`3.54e-6`, нижче tolerance `1e-5`).
- 80 тестів і compile check пройшли.

## Артефакти

- `Conference95_generated.docx`: `20db8e79ad55fbe2df98383e646a5617e1a2e59b335274e132d8a71c6d0e93b5`
- `Conference95_generated.pdf`: `eb6c3209ec96e65574dbffae7a501c49fb89ee82c84b39231db72ffc544c8eee`
- Повний перелік контрольних сум: `reports/FILES.sha256`.

## Blockers

Немає. Остаточне `ACCEPTED` встановлює Reviewer.

## Перевірка

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m journal_factory.cli build-journal --conference-id 95 --source <RAW_ZIP> --etalon ETALON-JOURNAL.docx --template Jurnal.dotx --source-pack <SOURCE_PACK> --conference-config fixtures\conferences\095\conference_metadata.json --typography-profile legacy_14pt --output build\iteration-004
.venv\Scripts\python -m journal_factory.cli render-journal --docx build\iteration-004\Conference95\Conference95_generated.docx --pdf build\iteration-004\Conference95\Conference95_generated.pdf --report build\iteration-004\Conference95\reports\render_report.json --expected-articles 34 --expected-first-article-page 8 --official-toc fixtures\conferences\095\official_toc.json
```

RAW, golden PDF і окремі сирі статті не комітяться. DOCX/PDF вручну не редагувалися; cloud LLM не використовувався.
