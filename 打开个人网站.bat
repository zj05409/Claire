@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "BUNDLED_PY=C:\Users\zj054\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED_PY%" (
  "%BUNDLED_PY%" "%~dp0tools\run_site.py"
) else (
  python "%~dp0tools\run_site.py"
)
pause
