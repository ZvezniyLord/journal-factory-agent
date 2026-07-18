# Протокол реальних тестів на хості

Цей протокол використовується, коли агент не може сам отримати великий RAW, запустити Word/LibreOffice, перевірити шрифти або виконати Windows COM automation.

## Коли створювати request

- потрібен реальний архів конференції;
- потрібен ETALON або DOTX з локального диска;
- потрібен Microsoft Word;
- потрібен LibreOffice render;
- потрібні встановлені шрифти;
- потрібна фактична PDF-пагінація;
- потрібен великий regression-run, який неможливо виконати в поточному середовищі.

## Формат request

Файл:

```text
reports/host_requests/REQ-<date>-<short-name>.json
```

Схема:

```json
{
  "request_id": "REQ-20260719-CONF95-BUILD",
  "branch": "agent/journal-builder-95",
  "commit": "<sha>",
  "conference_id": 95,
  "purpose": "Перший реальний production build",
  "required_files": [],
  "environment": {},
  "commands": [],
  "expected_outputs": [],
  "pass_conditions": [],
  "failure_collection": [],
  "privacy_notes": []
}
```

## Що має виконати Codex або користувач

1. Переключитися на вказану branch і commit.
2. Перевірити SHA-256 input files.
3. Виконати команди без ручного редагування output.
4. Зберегти stdout/stderr і exit code.
5. Не комітити великі RAW, приватні статті або фінальні журнали, якщо репозиторій для цього не призначений.
6. Закомітити лише reports, manifests, hashes, screenshots дозволеного обсягу та мінімальні anonymized fixtures.

## Формат відповіді

```text
reports/host_results/<request_id>/
  ENVIRONMENT.json
  COMMANDS.log
  RESULT.json
  FILES.sha256
  BLOCKERS.json
  render/
```

`RESULT.json` містить:

```json
{
  "request_id": "...",
  "status": "PASS|FAIL|BLOCKED",
  "started_at": "...",
  "finished_at": "...",
  "exit_codes": {},
  "outputs": [],
  "observations": [],
  "blockers": []
}
```

## Перша потрібна host-перевірка

Для Conference 95 потрібні:

- реальний `95.zip`;
- `ETALON-JOURNAL.docx`;
- `Jurnal.dotx`;
- official `Conference95.pdf`;
- Python 3.11+;
- LibreOffice або Microsoft Word;
- потрібні шрифти.

Агент має створити точний JSON request після появи першої робочої команди `build-journal`.

## Правило blocker

Host blocker блокує лише залежний крок. Архітектура, unit-тести, XML fixtures, schemas, база знань і CLI продовжують розроблятися.
