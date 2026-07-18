# Journal Factory: цикл Codex ↔ Reviewer

Актуальна задача зберігається у `coordination/CYCLE_STATE.json` гілки `agent/journal-control`.

## Маркери

- `READY_FOR_CODEX`: Codex виконує `next_action`.
- `READY_FOR_REVIEW`: результат запушено, Reviewer перевіряє.
- `CHANGES_REQUESTED`: Reviewer записав дефекти; Codex повторює цикл.
- `BLOCKED_NEEDS_USER`: потрібен зовнішній файл, доступ або host-тест.
- `ACCEPTED`: конференція пройшла всі gates.
- `SERIES_REGRESSION`: повторний прогін усієї прийнятої серії одним ruleset.
- `PROJECT_COMPLETE`: завершено всю серію і universality pass.

## Цикл Codex

1. `git fetch upstream --prune`.
2. Прочитати стан: `git show upstream/agent/journal-control:coordination/CYCLE_STATE.json`.
3. Працювати лише коли `owner=CODEX` і стан `READY_FOR_CODEX` або `CHANGES_REQUESTED`.
4. Оновити `work_branch` fast-forward.
5. Виконувати `next_action` циклічно: код → тести → DOCX → PDF → QA. Результат вручну не редагувати.
6. Після кожної змістовної зміни робити український коміт.
7. Запушити код, тести, згенерований DOCX/PDF і машинні звіти. RAW та окремі сирі статті не комітити.
8. У machine-state записати `READY_FOR_REVIEW`, commit SHA, артефакти, тести, blockers і передати owner `REVIEWER`.
9. Знову читати machine-state; при `CHANGES_REQUESTED` одразу починати нову ітерацію.

Codex не ставить `ACCEPTED` самостійно.

## Цикл Reviewer

При `READY_FOR_REVIEW` перевірити commit, DOCX, PDF, fidelity, структуру, TOC, пагінацію, шрифти, таблиці, рисунки, формули та відсутність ручних/номерних patches.

- Є дефекти: записати `review_findings`, конкретний `next_action`, збільшити iteration, поставити `CHANGES_REQUESTED`, owner `CODEX`.
- Усі gates пройдені: поставити `ACCEPTED`, зафіксувати SHA артефактів і перейти до наступної конференції.
- Після першого проходу всієї серії: `SERIES_REGRESSION` від 95 до останньої конференції.

## Артефакти

`artifacts/conferences/<ID>/iteration-<NNN>/` містить generated DOCX/PDF, `ITERATION_RESULT.json`, `REVIEW_PACKET.md`, QA reports і `FILES.sha256`.

Для Conference 95 профіль `legacy_14pt`. Нові профілі задаються явно, типовий новий — `standard_11pt`.

Користувач дозволив комітити згенеровані DOCX/PDF для рев’ю. Якщо репозиторій публічний, перед публікацією треба підтвердити, що зміст можна розкривати; великі файли зберігати через Git LFS або Actions artifacts.
