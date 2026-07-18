# Контрольована чистка Journal Factory

Мета: залишити в репозиторії тільки код Journal Factory, тести, конфігурацію, координацію, безпечні fixtures і дозволені результати.

## Видаляти

- кеші Python, pytest, IDE та ОС;
- тимчасові build-каталоги без затверджених артефактів;
- дублікати старих пакетів/релізів, які не імпортуються кодом і не згадані в актуальній документації;
- застарілі одноразові scripts, замінені новими модулями;
- випадкові файли, не пов’язані з Journal Factory;
- локальні untracked `Release-AI-Editor-5.5/` і `Release-AI-Editor-5.5-Public-src/`, якщо вони не потрібні жодному імпорту, тесту або source-pack contract.

## Зберігати

- `journal_factory/`, `tests/`, `schemas/`, `config/`, `.github/`;
- `skills/journal/`, `AGENTS.md`, `CODEX.md`, `PROJECT_STATUS.md`;
- `coordination/`, `docs/`, `knowledge_base/`;
- шаблони/fixtures, потрібні тестам;
- machine reports і згенеровані DOCX/PDF, дозволені користувачем;
- історичні файли, на які є активні імпорти або regression gates.

## Процедура

1. Створити `reports/repository_cleanup_inventory.json` зі списками `keep`, `delete`, `move`, `uncertain` і доказом для кожного шляху.
2. Перевірити імпорти, CI, документацію та тести.
3. Видаляти тільки `delete`; `uncertain` не чіпати.
4. Оновити `.gitignore` для `.venv`, `__pycache__`, `.pytest_cache`, локальних temp/build і приватних RAW.
5. Запустити повний pytest і compile check після чистки.
6. Зробити окремий український commit, щоб чистку можна було легко відкотити.

RAW-архіви й сирі статті не переміщувати в GitHub. Чистка не повинна видаляти файли на диску `N:` поза локальним checkout репозиторію.
