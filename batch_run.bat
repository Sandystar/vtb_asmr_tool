@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "CHECK_ONLY=0"
if /i "%~1"=="--check" set "CHECK_ONLY=1"

cd /d "%~dp0"
if errorlevel 1 goto :failure

set "REQUIRED_PYTHON_MAJOR=3"
set "REQUIRED_PYTHON_MINOR=13"
set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "DEPENDENCY_HASH_FILE=%VENV_DIR%\.installed-project-hash"
set "CURRENT_HASH_FILE=%VENV_DIR%\.current-project-hash"

call :find_python
if errorlevel 1 goto :failure
call :ensure_virtual_environment
if errorlevel 1 goto :failure
call :ensure_project_dependencies
if errorlevel 1 goto :failure
call :ensure_playwright_chromium
if errorlevel 1 goto :failure
call :ensure_local_config
if errorlevel 1 goto :failure

if "!CHECK_ONLY!"=="1" (
    echo [INFO] Environment and dependencies are ready.
    exit /b 0
)

echo [INFO] Starting GUI...
"%VENV_PYTHON%" -m spider_vtbasmr_gui
if errorlevel 1 goto :failure
exit /b 0

:find_python
set "PYTHON_LAUNCHER="
py -%REQUIRED_PYTHON_MAJOR%.%REQUIRED_PYTHON_MINOR% -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (%REQUIRED_PYTHON_MAJOR%, %REQUIRED_PYTHON_MINOR%) else 1)" >nul 2>&1
if not errorlevel 1 set "PYTHON_LAUNCHER=py -%REQUIRED_PYTHON_MAJOR%.%REQUIRED_PYTHON_MINOR%"

if not defined PYTHON_LAUNCHER (
    python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (%REQUIRED_PYTHON_MAJOR%, %REQUIRED_PYTHON_MINOR%) else 1)" >nul 2>&1
    if not errorlevel 1 set "PYTHON_LAUNCHER=python"
)

if defined PYTHON_LAUNCHER exit /b 0
echo [ERROR] Python %REQUIRED_PYTHON_MAJOR%.%REQUIRED_PYTHON_MINOR% is required.
echo [ERROR] Install it and run this script again.
exit /b 1

:ensure_virtual_environment
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (%REQUIRED_PYTHON_MAJOR%, %REQUIRED_PYTHON_MINOR%) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Rebuilding incompatible virtual environment...
        rmdir /s /q "%VENV_DIR%"
        if exist "%VENV_PYTHON%" exit /b 1
    )
)

if not exist "%VENV_PYTHON%" (
    echo [INFO] Creating Python %REQUIRED_PYTHON_MAJOR%.%REQUIRED_PYTHON_MINOR% virtual environment...
    %PYTHON_LAUNCHER% -m venv "%VENV_DIR%"
    if errorlevel 1 exit /b 1
)

"%VENV_PYTHON%" -m pip --version >nul 2>&1
if not errorlevel 1 exit /b 0

echo [INFO] Restoring pip...
"%VENV_PYTHON%" -m ensurepip --upgrade
if errorlevel 1 exit /b 1
exit /b 0

:ensure_project_dependencies
if not exist "pyproject.toml" (
    echo [ERROR] Missing dependency definition: pyproject.toml
    exit /b 1
)

"%VENV_PYTHON%" -c "from pathlib import Path; import hashlib; source=Path('pyproject.toml').read_bytes(); Path(r'%CURRENT_HASH_FILE%').write_text(hashlib.sha256(source).hexdigest(), encoding='ascii')"
if errorlevel 1 exit /b 1

set "PROJECT_HASH="
set /p PROJECT_HASH=<"%CURRENT_HASH_FILE%"
del /q "%CURRENT_HASH_FILE%" >nul 2>&1
if not defined PROJECT_HASH exit /b 1

set "INSTALLED_HASH="
if exist "%DEPENDENCY_HASH_FILE%" set /p INSTALLED_HASH=<"%DEPENDENCY_HASH_FILE%"
if not "!PROJECT_HASH!"=="!INSTALLED_HASH!" goto :install_project_dependencies

call :project_dependencies_healthy
if not errorlevel 1 exit /b 0

:install_project_dependencies
echo [INFO] Installing or repairing project dependencies...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check -e "."
if errorlevel 1 exit /b 1

call :project_dependencies_healthy
if errorlevel 1 exit /b 1

"%VENV_PYTHON%" -c "from pathlib import Path; Path(r'%DEPENDENCY_HASH_FILE%').write_text(r'!PROJECT_HASH!', encoding='ascii')"
if errorlevel 1 exit /b 1
exit /b 0

:project_dependencies_healthy
"%VENV_PYTHON%" -c "import playwright.sync_api; import PySide6.QtWidgets; import spider_vtbasmr_gui" >nul 2>&1
if errorlevel 1 exit /b 1
"%VENV_PYTHON%" -m pip check >nul 2>&1
if errorlevel 1 exit /b 1
exit /b 0

:ensure_playwright_chromium
echo [INFO] Checking Playwright Chromium...
call :playwright_chromium_ready
if not errorlevel 1 exit /b 0

echo [INFO] Installing Playwright Chromium...
set "PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=120000"
"%VENV_PYTHON%" -m playwright install chromium
if errorlevel 1 exit /b 1

call :playwright_chromium_ready
if errorlevel 1 exit /b 1
exit /b 0

:playwright_chromium_ready
"%VENV_PYTHON%" -c "from pathlib import Path; from playwright.sync_api import sync_playwright; driver=sync_playwright().start(); chromium=Path(driver.chromium.executable_path); revision=chromium.parents[1].name.removeprefix('chromium-'); headless=chromium.parents[2] / ('chromium_headless_shell-' + revision) / 'chrome-headless-shell-win64' / 'chrome-headless-shell.exe'; driver.stop(); raise SystemExit(0 if chromium.is_file() and headless.is_file() else 1)" >nul 2>&1
exit /b %errorlevel%

:ensure_local_config
if not exist "config" (
    echo [INFO] Creating local config directory...
    mkdir "config"
    if errorlevel 1 exit /b 1
)

for %%F in (vtbasmr_base.json vtb_list.json fnos_baidu_netdisk.json 7zip.json) do (
    if not exist "config\%%F" (
        if not exist "config.sample\%%F" (
            echo [ERROR] Missing config template: config.sample\%%F
            exit /b 1
        )
        echo [INFO] Creating local config: config\%%F
        copy /y "config.sample\%%F" "config\%%F" >nul
        if errorlevel 1 exit /b 1
    )
)
exit /b 0

:failure
echo.
echo [ERROR] Startup failed. Review the error output above.
if "!CHECK_ONLY!"=="1" exit /b 1
pause
exit /b 1