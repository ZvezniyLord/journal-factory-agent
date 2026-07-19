# Conference 95 — iteration 002

Статус: `REVIEW_ARTIFACTS_READY`, не `ACCEPTED` і не production-ready.

## Результат

- Реальний RAW ZIP: 139 файлів інвентаризовано.
- Auto-manifest: 34 `ARTICLE`, 6 `DUPLICATE`, 99 `NON_ARTICLE`, 0 `REVIEW/BLOCKED`.
- Усі 34 статті мають `MATCHED`, confidence і provenance.
- Усі 14 legacy `.doc` прочитано через ізольовані read-only Word COM-сесії.
- Типографічний профіль: `legacy_14pt`, переданий через CLI.
- Source-to-final fidelity: `PASS`; втрат тексту, таблиць, рисунків, charts або embeddings не виявлено.
- Дві чисті збірки семантично ідентичні; різняться лише байти ZIP-контейнера DOCX.
- Microsoft Word 16.0 створив PDF на 241 сторінку; усі сторінки візуально перевірено.
- 61 тест пройшов, compile check пройшов.

## Артефакти

- `Conference95_generated.docx`: `b4fd0b75361e73a206d7c491fffe0d5da63814c9fda4e85a4506fa910b0f73f5`
- `Conference95_generated.pdf`: `2d1948c1c3d4d77a07da0e13051efab4f07857eacfb2a0524c08aa36119d3645`
- Повний перелік контрольних сум: `reports/FILES.sha256`.

## Blockers

- Front matter не параметризовано: сторінка 1 містить New York / June 12–14, а сторінки 2–3 і 241 — Cambridge / January 19–21 та conference 91.
- TOC field відсутній; 34 із 34 записів не сформовано.
- Наскрізна пагінація відсутня на PDF-сторінках 1–89; видима нумерація починається з `1` лише на PDF-сторінці 90.
- Номери й пробіли в назвах секцій не нормалізовані.

Офіційний PDF не використовувався і для цієї ітерації не потрібний. Локальний готовий `Conference95.docx` не був джерелом тексту чи складання.

## Перевірка

```powershell
.venv\Scripts\python -m pytest -p no:cacheprovider
.venv\Scripts\python -m journal_factory.cli build-journal --conference-id 95 --source <RAW_ZIP> --etalon ETALON-JOURNAL.docx --template Jurnal.dotx --source-pack <SOURCE_PACK> --typography-profile legacy_14pt --output build\journal_builder
.venv\Scripts\python -m journal_factory.cli render-journal --docx build\journal_builder\Conference95\Conference95_generated.docx --pdf build\journal_builder\Conference95\Conference95_generated.pdf --report build\journal_builder\Conference95\reports\render_report.json
```
