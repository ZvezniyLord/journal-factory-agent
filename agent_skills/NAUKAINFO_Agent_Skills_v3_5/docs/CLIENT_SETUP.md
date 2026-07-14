# Підключення до агентного клієнта

## MCP stdio server

Команда:

```powershell
C:\Path\To\python.exe X:\Path\To\NAUKAINFO_Agent_Skills_v1\mcp_server\server.py
```

Environment:

```text
NAUKAINFO_PROJECT_ROOT=X:\NAUKA_iNFO_Jornal\нова концепція
NAUKAINFO_PYTHON=C:\Users\Vint\AppData\Local\Python\bin\python.exe
```

Приклад generic MCP config:

```json
{
  "servers": {
    "naukainfo-journal": {
      "type": "stdio",
      "command": "C:\\Users\\Vint\\AppData\\Local\\Python\\bin\\python.exe",
      "args": ["X:\\Path\\NAUKAINFO_Agent_Skills_v1\\mcp_server\\server.py"],
      "env": {
        "NAUKAINFO_PROJECT_ROOT": "X:\\NAUKA_iNFO_Jornal\\нова концепція"
      }
    }
  }
}
```

Назви полів конфігурації різняться між клієнтами; використовуйте їхню актуальну MCP документацію.

## Skills

Додайте `skills/` як workspace skills directory або скопіюйте окремі skill folders у каталог skills вашого агента. `name` у кожному `SKILL.md` збігається з ім’ям папки.

## Рекомендований стартовий запит агенту

```text
Підготуй діагностичну збірку конференції. Спочатку прочитай project context, виконай preflight і scan. Не змінюй raw-root або ETALON. Покажи plan та попроси підтвердження перед build. Після build виконай DOCX і visual audit, quality gate та онови project memory.
```
