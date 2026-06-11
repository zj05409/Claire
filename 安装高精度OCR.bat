@echo off
set "PY=C:\Users\zj054\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PY%" set "PY=python"
echo Installing open-source PaddleOCR...
"%PY%" -m pip install --disable-pip-version-check --target "%~dp0tools\ocr_packages" paddleocr paddlepaddle
echo.
echo Installation finished. The OCR model will download automatically on first use.
pause
