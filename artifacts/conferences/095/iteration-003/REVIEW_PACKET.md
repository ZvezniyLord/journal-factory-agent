# Conference 95 — iteration 003

Статус: `READY_FOR_REVIEW`, не `ACCEPTED`.

## Результат

- Front matter матеріалізовано з явного metadata config: Oxford International Science Forum, Oxford, United Kingdom, February 6–8, 2026, Conference 95.
- Stale-marker audit: `PASS`, 0 згадок New York, Cambridge, Conference 91 та пов’язаних старих реквізитів.
- Word TOC: 1 поле, 34 записи статей рівня 2; усі сторінки збігаються з 34 article bookmarks.
- Layout стабілізувався за два послідовні однакові Word COM проходи; TOC займає сторінки 4–5.
- Пагінація: титульна сторінка рахується, але номер прихований; стаття 1 починається на physical/printed 6; видимі номери 2–237 присутні без пропусків.
- Назви секцій нормалізовано через `config/section_catalog.json`, без умов за conference id.
- Direct typography audit після Word save: 1 581 абзац, 7 583 runs, 7 532 body-runs ефективно 14 pt; 51 дозволений виняток класифіковано, blockers 0.
- Fidelity і object preservation: `PASS`; 34 статті присутні рівно один раз, object loss 0.
- Усі 237 PDF-сторінок перевірено raster-аудитом і contact sheets; порожніх сторінок, пропущених footer-номерів або видимих layout-дефектів не знайдено.
- Дві незалежні чисті збірки мають однаковий semantic snapshot, TOC/page mappings та 237 сторінок. Pixel comparison відрізняється на три канали одного пікселя сторінки 147, нижче tolerance `1e-5`.
- 73 тести та compile check пройшли.

## Артефакти

- `Conference95_generated.docx`: `3a5741f98e6dd59535f75d66d218660d92b3f8dee4e4c84b023dfcdcba26898e`
- `Conference95_generated.pdf`: `381e261a5e2b624477f6042cda6c6eba8ecc67bf30bd3d8029bba6b85bbc8203`
- Повний перелік контрольних сум: `reports/FILES.sha256`.

## Blockers

Немає. Остаточне `ACCEPTED` встановлює Reviewer.

## Перевірка

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m journal_factory.cli build-journal --conference-id 95 --source <RAW_ZIP> --etalon ETALON-JOURNAL.docx --template Jurnal.dotx --source-pack <SOURCE_PACK> --conference-config fixtures\conferences\095\conference_metadata.json --section-catalog config\section_catalog.json --typography-profile legacy_14pt --output build\iteration-003
.venv\Scripts\python -m journal_factory.cli render-journal --docx build\iteration-003\Conference95\Conference95_generated.docx --pdf build\iteration-003\Conference95\Conference95_generated.pdf --report build\iteration-003\Conference95\reports\render_report.json --expected-articles 34 --expected-first-article-page 6
```

Офіційний PDF у цій ітерації не потрібний. RAW та окремі сирі статті не комітяться; DOCX/PDF вручну не редагувалися.
