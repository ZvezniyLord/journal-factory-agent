# CODEX.md — коротка команда для Codex

## Команда

> Онови гілку `agent/journal-builder-95`, прочитай `AGENTS.md`, `PROJECT_STATUS.md` і `docs/PROJECT_EXECUTION_PLAN.md`. Продовжуй реалізацію production Journal Builder для Conference 95: RAW → DOCX → PDF → fidelity/render/regression reports. Не змінюй авторський текст, не додавай винятки за номером конференції, усі нові правила покрий тестами. Коли потрібен реальний Windows/Word/LibreOffice/шрифтовий тест, створи host request за `docs/HOST_TEST_PROTOCOL.md`. Після кожної завершеної ітерації зроби коміт українською мовою та онови `PROJECT_STATUS.md`.

## Початок роботи

```bash
git fetch origin
git switch agent/journal-builder-95
git pull --ff-only origin agent/journal-builder-95
python -m pip install -r requirements.txt
pytest -q
```

## Поточна ціль

Зібрати Conference 95 із реального RAW-архіву, а не лише проаналізувати його.

Мінімальний production flow:

```text
RAW archive
  → safe workspace
  → article manifest
  → source snapshots
  → article header parsing
  → allowed normalization
  → lossless DOCX/XML article transfer
  → ETALON assembly
  → TOC and pagination
  → DOCX render to PDF
  → source-to-final fidelity audit
  → regression gate
```

## Заборонено

- переписувати текст статті;
- видаляти або спрощувати таблиці, рисунки, формули чи виноски;
- створювати `if conference_id == 95` у загальних правилах;
- оголошувати production PASS без реального render/fidelity report;
- використовувати LLM як редактор DOCX/XML;
- мовчки обходити blocker.

## Що залишати в репозиторії

- код і тести;
- короткі українські commit messages;
- `reports/conferences/095/` із машинними звітами без великих приватних RAW-файлів;
- `reports/host_requests/` для тестів, які має виконати користувач на хості;
- оновлений `PROJECT_STATUS.md`.
