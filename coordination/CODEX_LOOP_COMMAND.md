# Команда для Codex

> Працюй у безперервному циклі за `upstream/agent/journal-control:coordination/CYCLE_STATE.json` і протоколом `coordination/LOOP.md`. Коли owner=CODEX та state=READY_FOR_CODEX або CHANGES_REQUESTED — виконай next_action повністю: онови work_branch, змінюй тільки код/правила, запускай тести, збирай DOCX і PDF без ручного редагування, публікуй артефакти та QA-звіти, після чого переведи state у READY_FOR_REVIEW і owner у REVIEWER. Потім знову читай state; при новому CHANGES_REQUESTED одразу продовжуй наступну ітерацію. Відсутність офіційного старого PDF не є blocker. Codex не ставить ACCEPTED самостійно.

Початок кожного циклу:

```bash
git fetch upstream --prune
git show upstream/agent/journal-control:coordination/CYCLE_STATE.json
git show upstream/agent/journal-control:coordination/LOOP.md
```
