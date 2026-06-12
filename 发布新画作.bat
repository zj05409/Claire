@echo off
set "BUNDLED_PY=C:\Users\zj054\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED_PY%" (
  "%BUNDLED_PY%" "%~dp0tools\publish_artwork.py"
) else (
  python "%~dp0tools\publish_artwork.py"
)
