@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "BUNDLED_PY=C:\Users\zj054\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%BUNDLED_PY%" (
  set "PYTHON_EXE=%BUNDLED_PY%"
) else (
  set "PYTHON_EXE=python"
)
"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install --target tools\camera_packages opencv-python
echo.
echo 拍照支持安装完成。现在可以重新打开发布工具，点击拍照按钮。
pause
