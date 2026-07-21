@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PYTHON_LAUNCHER="
py -3.13 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON_LAUNCHER=py -3.13"

if not defined PYTHON_LAUNCHER (
    python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_LAUNCHER=python"
)

if not defined PYTHON_LAUNCHER (
    echo [ERROR] Python 3.13 is required. Install it and run this script again.
    pause
    exit /b 1
)

set "VENV_PYTHON=.venv\Scripts\python.exe"
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Rebuilding .venv with Python 3.13...
        rmdir /s /q ".venv"
    )
)

if not exist "%VENV_PYTHON%" (
    echo [INFO] Creating Python 3.13 virtual environment...
    %PYTHON_LAUNCHER% -m venv ".venv"
    if errorlevel 1 goto :failure
    "%VENV_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto :failure
)

set "PROJECT_HASH_FILE=.venv\.current-project-hash"
"%VENV_PYTHON%" -c "from pathlib import Path; import hashlib; source=Path('pyproject.toml').read_bytes(); Path(r'%PROJECT_HASH_FILE%').write_text(hashlib.sha256(source).hexdigest(), encoding='ascii')"
if errorlevel 1 goto :failure
set /p PROJECT_HASH=<"%PROJECT_HASH_FILE%"
del /q "%PROJECT_HASH_FILE%"

set "INSTALLED_HASH="
if exist ".venv\.installed-project-hash" set /p INSTALLED_HASH=<".venv\.installed-project-hash"

if not "!PROJECT_HASH!"=="!INSTALLED_HASH!" (
    echo [INFO] Installing project dependencies...
    "%VENV_PYTHON%" -m pip install -e "."
    if errorlevel 1 goto :failure
    "%VENV_PYTHON%" -c "from pathlib import Path; Path('.venv/.installed-project-hash').write_text('!PROJECT_HASH!', encoding='ascii')"
    if errorlevel 1 goto :failure
)

"%VENV_PYTHON%" -m spider_vtbasmr_gui
if errorlevel 1 goto :failure
exit /b 0

:failure
echo.
echo [ERROR] GUI startup failed. Review the error output above.
pause
exit /b 1