@echo off
setlocal
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
  echo uv is not on PATH
  exit /b 1
)
uv run --no-project --with-requirements requirements.txt python -m journal_factory.launcher_gui
